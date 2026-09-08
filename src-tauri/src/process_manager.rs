use std::io::{Read, Write};
use std::net::{SocketAddr, TcpStream};
use std::path::PathBuf;
use std::process::Command;
use std::sync::{Arc, Mutex, RwLock};
use std::time::{Duration, Instant};
use tauri::Emitter;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

#[derive(Debug, Clone, serde::Serialize, serde::Deserialize)]
pub struct BackendStatus {
    pub state: String,
    pub is_healthy: bool,
    pub url: String,
    pub managed_by_tauri: bool,
    pub pid: Option<u32>,
    pub error: Option<String>,
}

impl Default for BackendStatus {
    fn default() -> Self {
        Self {
            state: "offline".to_string(),
            is_healthy: false,
            url: "http://127.0.0.1:8000".to_string(),
            managed_by_tauri: false,
            pid: None,
            error: None,
        }
    }
}

pub struct ProcessManager {
    pids: Arc<Mutex<Vec<u32>>>,
    status: Arc<RwLock<BackendStatus>>,
}

impl ProcessManager {
    pub fn new() -> Self {
        Self {
            pids: Arc::new(Mutex::new(Vec::new())),
            status: Arc::new(RwLock::new(BackendStatus::default())),
        }
    }

    pub fn get_status(&self) -> BackendStatus {
        self.status.read().unwrap().clone()
    }

    /// Checks whether the backend at 127.0.0.1:8000 is healthy by sending an HTTP GET /health request.
    pub fn check_backend_health(&self) -> bool {
        Self::probe_health("127.0.0.1:8000", Duration::from_millis(600))
    }

    fn probe_health(addr_str: &str, timeout: Duration) -> bool {
        let addr: SocketAddr = match addr_str.parse() {
            Ok(a) => a,
            Err(_) => return false,
        };

        if let Ok(mut stream) = TcpStream::connect_timeout(&addr, timeout) {
            let _ = stream.set_read_timeout(Some(timeout));
            let _ = stream.set_write_timeout(Some(timeout));
            let request = "GET /health HTTP/1.1\r\nHost: 127.0.0.1:8000\r\nConnection: close\r\n\r\n";
            if stream.write_all(request.as_bytes()).is_ok() {
                let mut buffer = [0u8; 1024];
                if let Ok(bytes_read) = stream.read(&mut buffer) {
                    let response = String::from_utf8_lossy(&buffer[..bytes_read]);
                    if response.contains("200 OK") {
                        return true;
                    }
                }
            }
        }
        false
    }

    /// Resolves the repository root directory containing backend/main.py.
    fn resolve_repo_root(&self) -> Option<PathBuf> {
        // 1. Try current working directory
        if let Ok(cwd) = std::env::current_dir() {
            if cwd.join("backend").join("main.py").exists() {
                return Some(cwd);
            }
            if let Some(parent) = cwd.parent() {
                if parent.join("backend").join("main.py").exists() {
                    return Some(parent.to_path_buf());
                }
            }
        }

        // 2. Try relative to the current executable
        if let Ok(exe_path) = std::env::current_exe() {
            let mut current = exe_path.as_path();
            while let Some(parent) = current.parent() {
                if parent.join("backend").join("main.py").exists() {
                    return Some(parent.to_path_buf());
                }
                current = parent;
            }
        }

        None
    }

    /// Starts the FastAPI backend (and in-process headless AI worker) if not already healthy.
    pub fn start_backend(&self, app_handle: &tauri::AppHandle) {
        log::info!("Initiating GestureForge backend runtime checks...");

        // 1. Prevent duplicate launches: if already healthy, do not spawn another instance
        if self.check_backend_health() {
            log::info!("Backend is already running and healthy at http://127.0.0.1:8000");
            {
                let mut status = self.status.write().unwrap();
                status.state = "healthy".to_string();
                status.is_healthy = true;
                status.managed_by_tauri = false;
                status.error = None;
            }
            let _ = app_handle.emit("backend-ready", serde_json::json!({
                "status": "healthy",
                "url": "http://127.0.0.1:8000",
                "managed_by_tauri": false
            }));
            return;
        }

        // 2. Locate repo root or bundled backend
        let repo_root = self.resolve_repo_root();
        log::info!("Resolved repository root: {:?}", repo_root);

        // Update status to starting
        {
            let mut status = self.status.write().unwrap();
            status.state = "starting".to_string();
            status.is_healthy = false;
        }

        // 3. Configure command based on debug/release and bundled executables
        let mut cmd: Command;
        let is_debug = cfg!(debug_assertions);

        // Check if bundled backend binary exists (for packaged builds)
        let bundled_exe = repo_root.as_ref().and_then(|root| {
            let candidate = root.join("bundled").join("backend.exe");
            if candidate.exists() {
                Some(candidate)
            } else {
                None
            }
        });

        if let Some(exe_path) = bundled_exe {
            log::info!("Launching bundled backend binary: {:?}", exe_path);
            cmd = Command::new(&exe_path);
            if let Some(ref root) = repo_root {
                cmd.current_dir(root);
            }
        } else {
            // Launch via `uv run uvicorn backend.main:app`
            log::info!(
                "Launching backend via uv run uvicorn (debug_reload={})...",
                is_debug
            );
            cmd = Command::new("uv");
            cmd.arg("run").arg("uvicorn").arg("backend.main:app");
            cmd.arg("--port").arg("8000").arg("--host").arg("127.0.0.1");

            if is_debug {
                cmd.arg("--reload");
            }

            if let Some(ref root) = repo_root {
                cmd.current_dir(root);
            }
        }

        #[cfg(windows)]
        {
            cmd.creation_flags(CREATE_NO_WINDOW);
        }

        // 4. Spawn child process
        match cmd.spawn() {
            Ok(child) => {
                let pid = child.id();
                log::info!("Successfully spawned backend process (PID: {})", pid);
                {
                    let mut pids = self.pids.lock().unwrap();
                    pids.push(pid);
                }
                {
                    let mut status = self.status.write().unwrap();
                    status.pid = Some(pid);
                    status.managed_by_tauri = true;
                }

                // 5. Poll /health until healthy (up to 30 seconds)
                let poll_start = Instant::now();
                let poll_timeout = Duration::from_secs(30);
                let mut healthy = false;

                while poll_start.elapsed() < poll_timeout {
                    std::thread::sleep(Duration::from_millis(300));
                    if self.check_backend_health() {
                        healthy = true;
                        break;
                    }
                }

                if healthy {
                    log::info!(
                        "GestureForge backend & AI perception worker are healthy after {:.1}s!",
                        poll_start.elapsed().as_secs_f32()
                    );
                    {
                        let mut status = self.status.write().unwrap();
                        status.state = "healthy".to_string();
                        status.is_healthy = true;
                        status.error = None;
                    }
                    let _ = app_handle.emit("backend-ready", serde_json::json!({
                        "status": "healthy",
                        "url": "http://127.0.0.1:8000",
                        "pid": pid,
                        "managed_by_tauri": true
                    }));
                } else {
                    let err_msg = "Backend failed to respond on /health within 30 seconds".to_string();
                    log::error!("{}", err_msg);
                    {
                        let mut status = self.status.write().unwrap();
                        status.state = "failed".to_string();
                        status.error = Some(err_msg.clone());
                    }
                    let _ = app_handle.emit("backend-error", serde_json::json!({
                        "status": "failed",
                        "error": err_msg
                    }));
                }
            }
            Err(e) => {
                let err_msg = format!("Failed to spawn backend process: {}", e);
                log::error!("{}", err_msg);
                {
                    let mut status = self.status.write().unwrap();
                    status.state = "failed".to_string();
                    status.error = Some(err_msg.clone());
                }
                let _ = app_handle.emit("backend-error", serde_json::json!({
                    "status": "failed",
                    "error": err_msg
                }));
            }
        }
    }

    /// Gracefully terminates all tracked child processes and their process trees.
    pub fn terminate_all(&self) {
        let mut pids = self.pids.lock().unwrap();
        if pids.is_empty() {
            return;
        }

        log::info!("Terminating managed child processes: {:?}", *pids);
        for pid in pids.drain(..) {
            log::info!("Killing process tree for PID {}", pid);
            #[cfg(windows)]
            {
                let mut kill_cmd = Command::new("taskkill");
                kill_cmd.args(["/F", "/T", "/PID", &pid.to_string()]);
                kill_cmd.creation_flags(CREATE_NO_WINDOW);
                let _ = kill_cmd.output();
            }
            #[cfg(not(windows))]
            {
                let _ = Command::new("kill").args(["-9", &pid.to_string()]).output();
            }
        }

        let mut status = self.status.write().unwrap();
        status.state = "offline".to_string();
        status.is_healthy = false;
        status.pid = None;
    }
}

impl Drop for ProcessManager {
    fn drop(&mut self) {
        self.terminate_all();
    }
}
