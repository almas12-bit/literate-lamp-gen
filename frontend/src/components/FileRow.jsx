import { useRef, useState, useEffect, useMemo } from 'react';
import { Trash2, Loader2, RefreshCw, Play, Pause } from 'lucide-react';
import { updateJob, deleteJob, retryFailed } from '../api';

const SS_CATS = [
  "Abstract","Animals/Wildlife","Arts","Backgrounds/Textures","Beauty/Fashion",
  "Buildings/Landmarks","Business/Finance","Celebrities","Education","Food and drink",
  "Healthcare/Medical","Holidays","Industrial","Interiors","Miscellaneous",
  "Nature","Objects","Parks/Outdoor","People","Religion","Science",
  "Signs/Symbols","Sports/Recreation","Technology","Transportation","Vintage"
];

const AS_CATS = [
  {v:"0",l:"— none —"},{v:"1",l:"1. Animals"},{v:"2",l:"2. Buildings and Architecture"},
  {v:"3",l:"3. Business"},{v:"4",l:"4. Drinks"},{v:"5",l:"5. The Environment"},
  {v:"6",l:"6. States of Mind"},{v:"7",l:"7. Food"},{v:"8",l:"8. Graphic Resources"},
  {v:"9",l:"9. Hobbies and Leisure"},{v:"10",l:"10. Industry"},{v:"11",l:"11. Landscapes"},
  {v:"12",l:"12. Lifestyle"},{v:"13",l:"13. People"},{v:"14",l:"14. Plants and Flowers"},
  {v:"15",l:"15. Culture and Religion"},{v:"16",l:"16. Science"},{v:"17",l:"17. Social Issues"},
  {v:"18",l:"18. Sports"},{v:"19",l:"19. Technology"},{v:"20",l:"20. Transport"},{v:"21",l:"21. Travel"}
];

const STATUS_CFG = {
  pending:   { label:'Pending',    cls:'status-pending'   },
  analyzing: { label:'Analyzing…', cls:'status-analyzing' },
  done:      { label:'✓ Done',      cls:'status-done'      },
  error:     { label:'✗ Error',     cls:'status-error'     },
  cancelled: { label:'Cancelled',  cls:'status-cancelled' },
};

export default function FileRow({ job, index, selected, onSelect, onDelete, onChange, activePlatforms }) {
  const videoRef = useRef(null);
  const [playing, setPlaying] = useState(false);
  const cfg = STATUS_CFG[job.status] || STATUS_CFG.pending;
  const kwCount = job.keywords ? job.keywords.split(',').filter(k => k.trim()).length : 0;
  const isVideo = job.media_type === 'video';
  const isVector = job.media_type === 'vector';
  const isDone = job.status === 'done';
  const isError = job.status === 'error';
  const showSS = activePlatforms.includes('shutterstock');
  const showAS = activePlatforms.includes('adobe_stock');

  // Create stable video URL using useMemo to prevent re-creation on every render
  const videoUrl = useMemo(() => {
    if (isVideo && job.fileObj) {
      return URL.createObjectURL(job.fileObj);
    }
    return null;
  }, [job.fileObj, isVideo]);

  // Create stable image URL using useMemo to prevent memory leak and flickering on every render
  const imageUrl = useMemo(() => {
    // Vector files (.ai/.eps) cannot be previewed directly in the browser
    if (!isVideo && !isVector && job.fileObj) {
      return URL.createObjectURL(job.fileObj);
    }
    return null;
  }, [job.fileObj, isVideo, isVector]);

  // Cleanup object URLs when component unmounts or fileObj changes
  useEffect(() => {
    return () => {
      if (videoUrl) URL.revokeObjectURL(videoUrl);
      if (imageUrl) URL.revokeObjectURL(imageUrl);
    };
  }, [videoUrl, imageUrl]);

  const patch = async (field, value) => {
    onChange(job.id, field, value);
    try { await updateJob(job.id, { [field]: value }); } catch {}
  };

  const handleDelete = async () => {
    try { await deleteJob(job.id); } catch {}
    onDelete(job.id);
  };

  const handleRetry = async () => {
    try { await retryFailed([job.id]); onChange(job.id, 'status', 'pending'); onChange(job.id, 'error', ''); } catch {}
  };

  const backendBase = 'http://localhost:8000';
  const effectiveVideoUrl = videoUrl || (isVideo && job.media_url ? `${backendBase}${job.media_url}` : null);
  const effectiveImageUrl = imageUrl || (!isVideo && job.media_url ? `${backendBase}${job.media_url}` : null);

  const togglePlay = (e) => {
    if (e) e.stopPropagation();
    if (!videoRef.current || !effectiveVideoUrl) return;
    
    if (playing) { 
      videoRef.current.pause(); 
      setPlaying(false); 
    } else { 
      videoRef.current.muted = true;
      const playPromise = videoRef.current.play();
      if (playPromise !== undefined) {
        playPromise
          .then(() => setPlaying(true))
          .catch(err => {
            console.error('Play failed:', err);
            setPlaying(false);
          });
      } else {
        setPlaying(true);
      }
    }
  };

  const selectStyle = (value) => ({
    width:'100%', padding:'5px 8px', fontSize:12,
    border:'1px solid var(--border)', borderRadius:'var(--radius)',
    background:'var(--bg-surface-2)', marginBottom:4
  });

  return (
    <div style={{
      background:'var(--bg-surface)', border:`1px solid ${selected ? 'var(--accent)' : 'var(--border)'}`,
      borderRadius:'var(--radius-lg)', overflow:'hidden', boxShadow: selected ? '0 0 0 2px var(--accent-light)' : 'var(--shadow-sm)',
      transition:'border-color 0.15s, box-shadow 0.15s'
    }}>
      {/* Status bar top */}
      <div style={{ height:3, background: job.status==='done'?'var(--success)': job.status==='error'?'var(--error)': job.status==='analyzing'?'var(--accent)':'var(--border)' }} />

      {/* Row header */}
      <div style={{ display:'flex', alignItems:'center', gap:8, padding:'7px 12px', background:'var(--bg-surface-2)', borderBottom:'1px solid var(--border)' }}>
        <div className={`cb-box ${selected ? 'checked' : ''}`} onClick={() => onSelect(job.id)}>
          {selected && <svg viewBox="0 0 10 8" width="9" height="9" fill="none" stroke="white" strokeWidth="2.5"><polyline points="1,4 3.5,6.5 9,1"/></svg>}
        </div>
        <span style={{ fontSize:11, color:'var(--text-tertiary)', fontWeight:600, minWidth:24 }}>#{String(index+1).padStart(2,'0')}</span>
        <span className={`pill ${cfg.cls}`} style={{ fontSize:10, display:'flex', alignItems:'center', gap:4 }}>
          {job.status === 'analyzing' && <Loader2 size={9} style={{ animation:'spin 0.8s linear infinite' }}/>}
          {cfg.label}
        </span>
        <span style={{ fontSize:12, color:'var(--text-secondary)', flex:1, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>{job.filename}</span>
        <span style={{ fontSize:10, fontWeight:700, padding:'2px 7px', borderRadius:4,
          background: isVideo ? 'rgba(123,45,139,0.1)' : isVector ? 'rgba(20,120,80,0.1)' : 'var(--accent-light)',
          color: isVideo ? '#7b2d8b' : isVector ? '#147850' : 'var(--accent)' }}>
          {isVideo ? 'VIDEO' : isVector ? 'VECTOR' : 'IMAGE'}
        </span>
        {isError && (
          <button className="btn btn-warning-soft btn-xs" onClick={handleRetry} style={{ flexShrink:0 }}>
            <RefreshCw size={10}/>Retry
          </button>
        )}
        {isError && job.error && (
          <span style={{ fontSize:11, color:'var(--error)', maxWidth:180, overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }} title={job.error}>{job.error}</span>
        )}
        <button onClick={handleDelete} style={{ background:'none', border:'none', cursor:'pointer', color:'var(--text-tertiary)', padding:2, flexShrink:0 }}
          onMouseEnter={e => e.currentTarget.style.color='var(--error)'}
          onMouseLeave={e => e.currentTarget.style.color='var(--text-tertiary)'}>
          <Trash2 size={13}/>
        </button>
      </div>

      {/* Row body */}
      <div style={{ display:'grid', gridTemplateColumns:'88px 1fr 1fr 210px' }}>
        {/* Thumbnail */}
        <div style={{ padding:10, display:'flex', alignItems:'flex-start', justifyContent:'center' }}>
          <div style={{ width:68, height:68, borderRadius:'var(--radius)', overflow:'hidden', background:'var(--bg-surface-3)', position:'relative', flexShrink:0, border:'1px solid var(--border)' }}>
            {isVideo ? (
              <>
                {effectiveVideoUrl ? (
                  <>
                    <video 
                      ref={videoRef} 
                      src={effectiveVideoUrl}
                      preload="metadata"
                      playsInline
                      style={{ width:'100%', height:'100%', objectFit:'cover', display: 'block' }}
                      onEnded={() => setPlaying(false)} 
                      onPause={() => setPlaying(false)}
                      onPlay={() => setPlaying(true)}
                      loop={false} 
                      muted
                    />
                    <div onClick={togglePlay} style={{ position:'absolute', inset:0, display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer', background:'rgba(0,0,0,0.25)' }}>
                      <div style={{ width:22, height:22, background:'rgba(0,0,0,0.55)', borderRadius:'50%', display:'flex', alignItems:'center', justifyContent:'center' }}>
                        {playing ? <Pause size={10} color="white"/> : <Play size={10} color="white"/>}
                      </div>
                    </div>
                  </>
                ) : (
                  <div title="Preview tidak tersedia" style={{ width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22 }}>🎬</div>
                )}
              </>
            ) : isVector ? (
              <div title="Vector file (.ai/.eps)" style={{ width:'100%', height:'100%', display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', gap:2 }}>
                <span style={{ fontSize:18 }}>🖊️</span>
                <span style={{ fontSize:8, fontWeight:700, color:'#147850', letterSpacing:'0.05em' }}>{(job.filename||\'\').split(\'.\'  ).pop().toUpperCase()}</span>
              </div>
            ) : effectiveImageUrl ? (
              <img src={effectiveImageUrl} alt="" style={{ width:'100%', height:'100%', objectFit:'cover' }}/>
            ) : (
              <div title="Preview tidak tersedia" style={{ width:'100%', height:'100%', display:'flex', alignItems:'center', justifyContent:'center', fontSize:22 }}>🖼️</div>
            )}
          </div>
        </div>

        {/* Title/Description */}
        <div style={{ padding:'10px 10px 10px 0', borderLeft:'1px solid var(--bg-surface-3)' }}>
          <p className="label-xs" style={{ marginBottom:5 }}>Title / Description</p>
          <textarea value={job.title} onChange={e => patch('title', e.target.value)} rows={4} placeholder={isDone ? '' : 'Will be filled after analysis…'}
            style={{ width:'100%', padding:'6px 8px', resize:'none', fontSize:12, lineHeight:1.5, background:'var(--bg-surface-2)' }}/>
          <p style={{ fontSize:10, color: (job.title||'').length > 200 ? 'var(--error)' : 'var(--text-tertiary)', textAlign:'right', marginTop:3 }}>
            {(job.title||'').length}/200
          </p>
        </div>

        {/* Keywords */}
        <div style={{ padding:'10px', borderLeft:'1px solid var(--bg-surface-3)' }}>
          <p className="label-xs" style={{ marginBottom:5 }}>Keywords</p>
          <textarea value={job.keywords} onChange={e => patch('keywords', e.target.value)} rows={4} placeholder={isDone ? '' : 'Will be filled after analysis…'}
            style={{ width:'100%', padding:'6px 8px', resize:'none', fontSize:12, lineHeight:1.5, background:'var(--bg-surface-2)' }}/>
          <p style={{ fontSize:10, color: kwCount > 49 ? 'var(--error)' : 'var(--text-tertiary)', textAlign:'right', marginTop:3 }}>
            {kwCount}/49 keywords
          </p>
        </div>

        {/* Categories + Flags */}
        <div style={{ padding:'10px', borderLeft:'1px solid var(--bg-surface-3)', display:'flex', flexDirection:'column', gap:8 }}>

          {/* Shutterstock categories */}
          {showSS && (
            <div>
              <div style={{ display:'flex', alignItems:'center', gap:5, marginBottom:5 }}>
                <span style={{ fontSize:9, fontWeight:700, padding:'1px 6px', borderRadius:3, background:'var(--accent-light)', color:'var(--accent)' }}>SS</span>
                <p className="label-xs">Shutterstock</p>
              </div>
              <select value={job.ss_category1} onChange={e => patch('ss_category1', e.target.value)} style={selectStyle()}>
                <option value="">Category 1</option>
                {SS_CATS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <select value={job.ss_category2} onChange={e => patch('ss_category2', e.target.value)} style={selectStyle()}>
                <option value="">Category 2 (optional)</option>
                {SS_CATS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          )}

          {/* Adobe Stock categories */}
          {showAS && (
            <div>
              <div style={{ display:'flex', alignItems:'center', gap:5, marginBottom:5 }}>
                <span style={{ fontSize:9, fontWeight:700, padding:'1px 6px', borderRadius:3, background:'#fde8e8', color:'#d7373f' }}>AS</span>
                <p className="label-xs">Adobe Stock</p>
              </div>
              <select value={job.as_category1||"0"} onChange={e => patch('as_category1', e.target.value)} style={selectStyle()}>
                {AS_CATS.map(c => <option key={c.v} value={c.v}>{c.l}</option>)}
              </select>
              <select value={job.as_category2||"0"} onChange={e => patch('as_category2', e.target.value)} style={selectStyle()}>
                {AS_CATS.map(c => <option key={c.v} value={c.v}>{c.l}</option>)}
              </select>
              <input value={job.releases||''} onChange={e => patch('releases', e.target.value)}
                placeholder="Releases (optional)"
                style={{ width:'100%', padding:'5px 8px', fontSize:12, border:'1px solid var(--border)', borderRadius:'var(--radius)', background:'var(--bg-surface-2)' }}
              />
            </div>
          )}

          {/* Flags */}
          <div style={{ borderTop:'1px solid var(--border)', paddingTop:7 }}>
            {[['editorial','Editorial'],['mature_content','Mature Content'],['illustration','Illustration']].map(([field, label]) => (
              <label key={field} style={{ display:'flex', alignItems:'center', gap:7, cursor:'pointer', marginBottom:5 }}>
                <div className={`cb-box ${job[field]==='yes' ? 'checked' : ''}`} style={{ width:13, height:13 }}
                  onClick={() => patch(field, job[field]==='yes' ? 'no' : 'yes')}>
                  {job[field]==='yes' && <svg viewBox="0 0 10 8" width="8" height="8" fill="none" stroke="white" strokeWidth="2.5"><polyline points="1,4 3.5,6.5 9,1"/></svg>}
                </div>
                <span style={{ fontSize:12, color:'var(--text-secondary)' }}>{label}</span>
              </label>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
