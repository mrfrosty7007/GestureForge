import React from 'react';
import { Sparkles, Terminal, Layers } from 'lucide-react';

export default function Header() {
  return (
    <header className="header-wrapper">
      <div className="header-inner">
        <a href="/" className="brand-group">
          <div className="brand-icon">
            <Sparkles size={22} />
          </div>
          <div>
            <span className="brand-name">GestureForge</span>
          </div>
        </a>

        <div className="header-meta">
          <span className="header-tag">
            <Terminal size={12} style={{ display: 'inline', marginRight: 4 }} />
            Phase 0: Foundation
          </span>
          <span className="header-tag">
            <Layers size={12} style={{ display: 'inline', marginRight: 4 }} />
            v0.1.0
          </span>
        </div>
      </div>
    </header>
  );
}
