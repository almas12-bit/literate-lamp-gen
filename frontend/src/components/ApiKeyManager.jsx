import { useState } from 'react';
import { Key, CheckCircle, Clock, AlertTriangle, ChevronDown, ChevronUp, Save, Zap } from 'lucide-react';
import { setKeys, testKeys } from '../api';

export default function ApiKeyManager({ keysInfo, onKeysUpdated }) {
  const [open, setOpen] = useState(false);
  const [text, setText] = useState('');
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [msg, setMsg] = useState({ type: '', text: '' });

  const active  = keysInfo.filter(k => k.status === 'active').length;
  const limited = keysInfo.filter(k => k.status === 'rate_limited').length;
  const errors  = keysInfo.filter(k => k.status === 'error').length;

  const handleSave = async () => {
    if (!text.trim()) return;
    setSaving(true);
    setMsg({ type: '', text: '' });
    try {
      const res = await setKeys(text);
      setMsg({ type: 'success', text: `✓ ${res.data.count} key(s) disimpan ke sistem!` });
      onKeysUpdated?.();
      setTimeout(() => setMsg({ type: '', text: '' }), 4000);
    } catch (err) {
      setMsg({ type: 'error', text: 'Gagal menyimpan API key' });
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setMsg({ type: 'info', text: 'Menguji koneksi ke Google AI Studio...' });
    try {
      const res = await testKeys();
      if (res.data.ok) {
        setMsg({ type: 'success', text: `✓ ${res.data.message}` });
      } else {
        setMsg({ type: 'error', text: `✗ ${res.data.message}` });
      }
      onKeysUpdated?.();
    } catch (err) {
      const detail = err.response?.data?.message || err.message || 'Koneksi gagal';
      setMsg({ type: 'error', text: `✗ Gagal tes koneksi: ${detail}` });
    } finally {
      setTesting(false);
    }
  };

  const statusCfg = {
    active:       { icon: <CheckCircle size={9}/>, cls: 'pill-success' },
    rate_limited: { icon: <Clock size={9}/>,        cls: 'pill-warning' },
    error:        { icon: <AlertTriangle size={9}/>, cls: 'pill-error'  },
  };

  return (
    <div className="card overflow-hidden">
      <button onClick={() => setOpen(o => !o)} style={{ width:'100%', display:'flex', alignItems:'center', justifyContent:'space-between', padding:'11px 14px', background:'none', border:'none', cursor:'pointer' }}>
        <div style={{ display:'flex', alignItems:'center', gap:8 }}>
          <Key size={14} style={{ color:'var(--accent)' }} />
          <span style={{ fontSize:13, fontWeight:600 }}>API Keys</span>
          <div style={{ display:'flex', gap:5 }}>
            {active  > 0 && <span className="pill pill-success" style={{fontSize:10}}>{active} active</span>}
            {limited > 0 && <span className="pill pill-warning" style={{fontSize:10}}>{limited} limited</span>}
            {errors  > 0 && <span className="pill pill-error"   style={{fontSize:10}}>{errors} error</span>}
            {keysInfo.length === 0 && <span className="pill pill-neutral" style={{fontSize:10}}>No keys</span>}
          </div>
        </div>
        {open ? <ChevronUp size={13} style={{color:'var(--text-tertiary)'}}/> : <ChevronDown size={13} style={{color:'var(--text-tertiary)'}}/>}
      </button>

      {open && (
        <div style={{ borderTop:'1px solid var(--border)', padding:14, display:'flex', flexDirection:'column', gap:10 }}>
          <div>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:6 }}>
              <p className="label-xs">Paste API Keys (satu per baris)</p>
              <span style={{ fontSize:11, color:'var(--text-tertiary)' }}>Mendukung format lama (AIza...) & format baru (AQ...)</span>
            </div>
            <textarea value={text} onChange={e => setText(e.target.value)} rows={4}
              placeholder={"AQ.AbCdEf1234567890...\natau\nAIzaSyAbCdEf1234567890..."}
              style={{ width:'100%', padding:'8px 10px', resize:'none', fontFamily:"'Source Code Pro',monospace", fontSize:12, lineHeight:1.7, background:'var(--bg-surface-2)' }}
            />
          </div>

          <div style={{ display:'flex', alignItems:'center', gap:10, flexWrap:'wrap' }}>
            <button className="btn btn-primary btn-sm" onClick={handleSave} disabled={saving || !text.trim()}>
              <Save size={12}/>{saving ? 'Menyimpan…' : 'Simpan Keys'}
            </button>
            <button className="btn btn-secondary btn-sm" onClick={handleTest} disabled={testing || keysInfo.length === 0}>
              <Zap size={12}/>{testing ? 'Menguji…' : 'Tes Koneksi'}
            </button>
            {msg.text && (
              <span style={{
                fontSize:12,
                color: msg.type === 'success' ? 'var(--success)' : msg.type === 'error' ? 'var(--danger, #ef4444)' : 'var(--text-secondary)',
                fontWeight: 500
              }}>
                {msg.text}
              </span>
            )}
          </div>

          {keysInfo.length > 0 && (
            <div>
              <p className="label-xs" style={{ marginBottom:6 }}>Status Key Terdaftar ({keysInfo.length})</p>
              <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
                {keysInfo.map((k,i) => {
                  const c = statusCfg[k.status] || statusCfg.active;
                  return (
                    <span
                      key={i}
                      className={`pill ${c.cls}`}
                      title={k.error ? `Error: ${k.error}` : 'Key Siap Digunakan'}
                      style={{ fontSize:11, fontFamily:"'Source Code Pro',monospace", display:'inline-flex', alignItems:'center', gap:4, cursor: k.error ? 'help' : 'default' }}
                    >
                      {c.icon}{k.key}
                      {k.error && (
                        <span style={{ fontSize:10, opacity:0.85, maxWidth:200, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                          — {k.error}
                        </span>
                      )}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
