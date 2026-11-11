import { setPlatforms } from '../api';

const PLATFORMS = [
  { id: 'shutterstock', label: 'Shutterstock', short: 'SS', color: '#1473e6', bg: '#e8f1fc' },
  { id: 'adobe_stock',  label: 'Adobe Stock',  short: 'AS', color: '#d7373f', bg: '#fde8e8' },
  { id: 'magnific',     label: 'Magnific',     short: 'MG', color: '#7c3aed', bg: '#f3e8ff' },
];

export default function PlatformSelector({ active, onChange }) {
  const toggle = async (id) => {
    const next = active.includes(id) ? active.filter(p => p !== id) : [...active, id];
    if (next.length === 0) return;
    try { await setPlatforms(next); onChange(next); } catch {}
  };
  return (
    <div className="card" style={{ padding:'11px 14px' }}>
      <p className="label-xs" style={{ marginBottom:8 }}>Platforms</p>
      <div style={{ display:'flex', flexDirection:'column', gap:7 }}>
        {PLATFORMS.map(p => {
          const on = active.includes(p.id);
          return (
            <label key={p.id} style={{ display:'flex', alignItems:'center', gap:8, cursor:'pointer' }}>
              <div className={`cb-box ${on ? 'checked' : ''}`} onClick={() => toggle(p.id)}>
                {on && <svg viewBox="0 0 10 8" width="9" height="9" fill="none" stroke="white" strokeWidth="2.5"><polyline points="1,4 3.5,6.5 9,1"/></svg>}
              </div>
              <span style={{ fontSize:13, fontWeight:500 }}>{p.label}</span>
              <span style={{ fontSize:10, fontWeight:700, padding:'1px 7px', borderRadius:3, background:p.bg, color:p.color, marginLeft:'auto' }}>{p.short}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}
