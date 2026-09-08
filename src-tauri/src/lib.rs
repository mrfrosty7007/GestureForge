mod process_manager;

use std::sync::Arc;
use process_manager::{BackendStatus, ProcessManager};

#[tauri::command]
fn get_backend_status(
    manager: tauri::State<'_, Arc<ProcessManager>>,
) -> BackendStatus {
    manager.get_status()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let process_manager = Arc::new(ProcessManager::new());

    tauri::Builder::default()
        .manage(process_manager.clone())
        .invoke_handler(tauri::generate_handler![get_backend_status])
        .setup({
            let pm = process_manager.clone();
            move |app| {
                if cfg!(debug_assertions) {
                    app.handle().plugin(
                        tauri_plugin_log::Builder::default()
                            .level(log::LevelFilter::Info)
                            .build(),
                    )?;
                }

                let handle = app.handle().clone();
                std::thread::spawn(move || {
                    pm.start_backend(&handle);
                });

                Ok(())
            }
        })
        .on_window_event({
            let pm = process_manager.clone();
            move |_window, event| {
                if let tauri::WindowEvent::CloseRequested { .. } | tauri::WindowEvent::Destroyed = event {
                    pm.terminate_all();
                }
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run({
            let pm = process_manager.clone();
            move |_app_handle, event| {
                if let tauri::RunEvent::ExitRequested { .. } | tauri::RunEvent::Exit = event {
                    pm.terminate_all();
                }
            }
        });
}
