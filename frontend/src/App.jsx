import { useState, useEffect, useCallback, useRef } from 'react';
import { Gem, Download, UploadCloud, Sun, Moon, Wifi, WifiOff, ServerCrash, ChevronDown } from 'lucide-react';
import {
  healthCheck, getModels, getKeysStatus, uploadFiles,
  getQueueStatus, getQueueJobs, startQueue, pauseQueue,
  stopQueue, resetQueue, retryFailed, deleteJobs
} from './api';
import ApiKeyManager    from './components/ApiKeyManager';
import ModelSelector    from './components/ModelSelector';
import PlatformSelector from './components/PlatformSelector';
import KeywordCount     from './components/KeywordCount';
import PromptRules      from './components/PromptRules';
import QueueControls    from './components/QueueControls';
import FilterBar        from './components/FilterBar';
import FileRow          from './components/FileRow';

const AS_CAT_MAP = {
  "1":"Animals","2":"Buildings and Architecture","3":"Business","4":"Drinks","5":"The Environment",
  "6":"States of Mind","7":"Food","8":"Graphic Resources","9":"Hobbies and Leisure","10":"Industry",
  "11":"Landscapes","12":"Lifestyle","13":"People","14":"Plants and Flowers","15":"Culture and Religion",
  "16":"Science","17":"Social Issues","18":"Sports","19":"Technology","20":"Transport","21":"Travel"
};

export default function App() {
  const [theme, setTheme]               = useState('light');
  const [models, setModels]             = useState([]);
  const [currentModel, setCurrentModel] = useState('gemini-2.5-flash');
  const [platforms, setPlatforms]       = useState(['shutterstock','adobe_stock']);
  const [kwCount, setKwCount]           = useState(45);
  const [keysInfo, setKeysInfo]         = useState([]);
  const [jobs, setJobs]                 = useState([]);
  const [fileObjs, setFileObjs]         = useState({});
  const [queueStatus, setQueueStatus]   = useState({});
  const [isDragging, setIsDragging]     = useState(false);
  const [backendOk, setBackendOk]       = useState(null);
  const [ffmpegOk, setFfmpegOk]         = useState(null);
  const [filter, setFilter]             = useState('all');
  const [sort, setSort]                 = useState('upload');
  const [selected, setSelected]         = useState([]);
  const [showExport, setShowExport]     = useState(false);
  const [exportPlatforms, setExportPlatforms] = useState(['shutterstock','adobe_stock']);
  const [rules, setRulesState]          = useState(null);
  const pollRef = useRef(null);
  const exportRef = useRef(null);

  // Theme
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Close export dropdown on outside click
  useEffect(() => {
    const handler = (e) => { if (exportRef.current && !exportRef.current.contains(e.target)) setShowExport(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const poll = useCallback(async () => {
    try {
      const [statusRes, jobsRes, keysRes] = await Promise.all([getQueueStatus(), getQueueJobs(), getKeysStatus()]);
      setQueueStatus(statusRes.data);
      setJobs(prev => {
        const newJobs = jobsRes.data.jobs;
        return newJobs.map(nj => ({ ...nj, fileObj: prev.find(pj => pj.id === nj.id)?.fileObj || null }));
      });
      setKeysInfo(keysRes.data.keys);
      setBackendOk(true);
    } catch { setBackendOk(false); }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const h = await healthCheck();
        setBackendOk(true);
        setFfmpegOk(h.data.ffmpeg);
        setCurrentModel(h.data.model || 'gemini-2.5-flash');
        setPlatforms(h.data.platforms || ['shutterstock']);
        setKwCount(h.data.keyword_count || 45);
        if (h.data.rules) setRulesState(h.data.rules);
      } catch { setBackendOk(false); }
    })();
    getModels().then(r => setModels(r.data.models)).catch(() => {});
    poll();
    pollRef.current = setInterval(poll, 2000);
    return () => clearInterval(pollRef.current);
  }, [poll]);

  const handleFiles = async (files) => {
    const form = new FormData();
    const fileArr = Array.from(files);
    fileArr.forEach(f => form.append('files', f));
    try {
      const res = await uploadFiles(form);
      const ids = res.data.job_ids;
      const newObjs = {};
      ids.forEach((id, i) => { if (fileArr[i]) newObjs[id] = fileArr[i]; });
      setFileObjs(prev => ({ ...prev, ...newObjs }));
      await poll();
    } catch (e) {
      alert(e?.response?.data?.detail || 'Upload failed. Did you add API keys?');
    }
  };

  const handleDrop = (e) => {
    e.preventDefault(); setIsDragging(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  };

  const handleJobChange = (id, field, value) => {
    setJobs(prev => prev.map(j => j.id === id ? { ...j, [field]: value } : j));
  };

  const handleJobDelete = (id) => {
    setJobs(prev => prev.filter(j => j.id !== id));
    setSelected(prev => prev.filter(s => s !== id));
  };

  // Filter + Sort
  const filteredJobs = jobs
    .filter(j => filter === 'all' || j.status === filter)
    .sort((a, b) => {
      if (sort === 'name_asc')  return a.filename.localeCompare(b.filename);
      if (sort === 'name_desc') return b.filename.localeCompare(a.filename);
      if (sort === 'status') {
        const order = { analyzing:0, error:1, pending:2, done:3, cancelled:4 };
        return (order[a.status]??5) - (order[b.status]??5);
      }
      return 0; // upload order
    });

  const allSelected = filteredJobs.length > 0 && filteredJobs.every(j => selected.includes(j.id));

  const handleSelectAll = () => {
    if (allSelected) setSelected([]);
    else setSelected(filteredJobs.map(j => j.id));
  };

  const handleDeleteSelected = async () => {
    if (!selected.length) return;
    try { await deleteJobs(selected); } catch {}
    setJobs(prev => prev.filter(j => !selected.includes(j.id)));
    setSelected([]);
  };

  const handleRetrySelected = async () => {
    try { await retryFailed(selected); } catch {}
    setJobs(prev => prev.map(j => selected.includes(j.id) && j.status === 'error' ? { ...j, status:'pending', error:'' } : j));
  };

  // CSV Export
  const exportCSV = (platform) => {
    const donJobs = jobs.filter(j => j.status === 'done');
    if (!donJobs.length) return;

    const sanitizeTitleExport = (t) => {
      let str = (t || '').trim();
      if (str.length > 200) {
        str = str.substring(0, 200);
        const lastSpace = str.lastIndexOf(' ');
        if (lastSpace > 50) str = str.substring(0, lastSpace);
        str = str.replace(/[,;:\-\s]+$/, '');
      }
      return str;
    };

    const sanitizeKeywordsExport = (kw) => {
      if (!kw) return '';
      const list = kw.split(',').map(k => k.trim()).filter(Boolean);
      return list.slice(0, 49).join(', ');
    };

    let csv = '';
    if (platform === 'shutterstock') {
      const headers = ['Filename','Description','Keywords','Categories','Editorial','Mature content','illustration'];
      const esc = s => `"${(s||'').replace(/"/g,'""')}"`;
      const rows = donJobs.map(j => {
        const cats = [j.ss_category1, j.ss_category2].filter(Boolean).join(', ');
        return [j.filename, esc(sanitizeTitleExport(j.title)), esc(sanitizeKeywordsExport(j.keywords)), esc(cats), j.editorial, j.mature_content, j.illustration].join(',');
      });
      csv = [headers.join(','), ...rows].join('\n');
      download(csv, 'shutterstock_metadata.csv');
    } else if (platform === 'adobe_stock') {
      const headers = ['Filename','Title','Keywords','Category','Releases'];
      const esc = s => `"${(s||'').replace(/"/g,'""')}"`;
      const rows = donJobs.map(j => {
        const cat = j.as_category1 && j.as_category1 !== '0' ? j.as_category1 : '';
        return [j.filename, esc(sanitizeTitleExport(j.title)), esc(sanitizeKeywordsExport(j.keywords)), cat, esc(j.releases||'')].join(',');
      });
      csv = [headers.join(','), ...rows].join('\n');
      download(csv, 'adobe_stock_metadata.csv');
    }
  };

  const download = (content, filename) => {
    const blob = new Blob([content], { type:'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const doneCount = jobs.filter(j => j.status === 'done').length;

  const toggleExportPlatform = (p) => {
    setExportPlatforms(prev => prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]);
  };

  return (
    <div style={{ minHeight:'100vh', background:'var(--bg-app)' }}>
      {/* Header */}
      <header style={{
        position:'sticky', top:0, zIndex:100,
        height:'var(--header-h)', background:'var(--bg-surface)',
        borderBottom:'1px solid var(--border)', boxShadow:'var(--shadow-sm)',
        display:'flex', alignItems:'center', padding:'0 24px', gap:12
      }}>
        {/* Logo */}
        <div style={{ display:'flex', alignItems:'center', gap:10 }}>
          <div style={{ width:30, height:30, background:'var(--accent)', borderRadius:'var(--radius)', display:'flex', alignItems:'center', justifyContent:'center' }}>
            <Gem size={16} color="white"/>
          </div>
          <div>
            <div style={{ fontSize:14, fontWeight:700, letterSpacing:'-0.3px', lineHeight:1.2 }}>
              Litterate<span style={{ color:'var(--accent)' }}> Lamp</span>
            </div>
            <div style={{ fontSize:10, color:'var(--text-tertiary)', textTransform:'uppercase', letterSpacing:'0.05em', lineHeight:1.2 }}>Metadata Generator</div>
          </div>
        </div>

        <div style={{ flex:1 }} />

        {/* Backend status */}
        <div style={{ display:'flex', alignItems:'center', gap:5, fontSize:11, fontWeight:600 }}>
          {backendOk === null ? <span style={{ color:'var(--text-tertiary)' }}>Connecting…</span>
            : backendOk ? <>
                <Wifi size={12} style={{ color:'var(--success)' }}/>
                <span style={{ color:'var(--success)' }}>Backend OK</span>
                {ffmpegOk === false && <span style={{ color:'var(--warning)', marginLeft:6 }}>⚠ ffmpeg missing</span>}
              </>
            : <><WifiOff size={12} style={{ color:'var(--error)' }}/><span style={{ color:'var(--error)' }}>Backend Down</span></>}
        </div>

        {/* Theme toggle */}
        <button onClick={() => setTheme(t => t === 'light' ? 'dark' : 'light')}
          style={{ width:32, height:32, borderRadius:'var(--radius)', border:'1px solid var(--border)', background:'var(--bg-surface-2)', display:'flex', alignItems:'center', justifyContent:'center', cursor:'pointer' }}>
          {theme === 'light' ? <Moon size={14} style={{ color:'var(--text-secondary)' }}/> : <Sun size={14} style={{ color:'var(--text-secondary)' }}/>}
        </button>

        {/* Export dropdown */}
        <div ref={exportRef} style={{ position:'relative' }}>
          <button className="btn btn-primary btn-sm" onClick={() => setShowExport(s => !s)} disabled={doneCount === 0}>
            <Download size={13}/>Export CSV ({doneCount}) <ChevronDown size={11}/>
          </button>
          {showExport && (
            <div style={{
              position:'absolute', right:0, top:38, background:'var(--bg-surface)',
              border:'1px solid var(--border)', borderRadius:'var(--radius-lg)',
              boxShadow:'var(--shadow-md)', padding:10, minWidth:220, zIndex:200
            }}>
              <p className="label-xs" style={{ padding:'2px 6px 8px' }}>Export for platform</p>
              {[
                { id:'shutterstock', label:'Shutterstock', file:'shutterstock_metadata.csv' },
                { id:'adobe_stock',  label:'Adobe Stock',  file:'adobe_stock_metadata.csv'  },
              ].map(p => (
                <div key={p.id}
                  onClick={() => toggleExportPlatform(p.id)}
                  style={{ display:'flex', alignItems:'center', gap:10, padding:'7px 8px', borderRadius:'var(--radius)', cursor:'pointer' }}
                  onMouseEnter={e => e.currentTarget.style.background='var(--bg-hover)'}
                  onMouseLeave={e => e.currentTarget.style.background='transparent'}
                >
                  <div className={`cb-box ${exportPlatforms.includes(p.id) ? 'checked' : ''}`} style={{ width:14, height:14 }}>
                    {exportPlatforms.includes(p.id) && <svg viewBox="0 0 10 8" width="9" height="9" fill="none" stroke="white" strokeWidth="2.5"><polyline points="1,4 3.5,6.5 9,1"/></svg>}
                  </div>
                  <div>
                    <div style={{ fontSize:13, fontWeight:500 }}>{p.label}</div>
                    <div style={{ fontSize:10, color:'var(--text-tertiary)', fontFamily:"'Source Code Pro',monospace" }}>{p.file}</div>
                  </div>
                </div>
              ))}
              <div style={{ height:1, background:'var(--border)', margin:'8px 0' }} />
              <button className="btn btn-primary btn-sm" style={{ width:'100%', justifyContent:'center' }}
                onClick={() => { exportPlatforms.forEach(p => exportCSV(p)); setShowExport(false); }}
                disabled={exportPlatforms.length === 0}>
                <Download size={12}/>Download {exportPlatforms.length} File{exportPlatforms.length !== 1 ? 's' : ''}
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main */}
      <main style={{ maxWidth:1100, margin:'0 auto', padding:'20px 24px', display:'flex', flexDirection:'column', gap:12 }}>

        {/* Backend offline banner */}
        {backendOk === false && (
          <div style={{ display:'flex', alignItems:'center', gap:10, padding:'10px 14px', background:'var(--error-bg)', border:'1px solid var(--error-border)', borderRadius:'var(--radius-lg)' }}>
            <ServerCrash size={15} style={{ color:'var(--error)', flexShrink:0 }} />
            <span style={{ fontSize:13 }}>
              <strong style={{ color:'var(--error)' }}>Backend not running. </strong>
              <span style={{ color:'var(--text-secondary)' }}>Run: </span>
              <code style={{ background:'var(--bg-surface-3)', padding:'1px 6px', borderRadius:3, fontSize:12, fontFamily:"'Source Code Pro',monospace" }}>
                cd backend && python -m uvicorn main:app --reload --port 8000
              </code>
            </span>
          </div>
        )}

        {/* Config panel — 4 columns */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 160px 140px', gap:10 }}>
          <ApiKeyManager keysInfo={keysInfo} onKeysUpdated={poll} />
          <ModelSelector models={models} currentModel={currentModel} onModelChange={setCurrentModel} />
          <PlatformSelector active={platforms} onChange={setPlatforms} />
          <KeywordCount value={kwCount} onChange={setKwCount} />
        </div>

        {/* Custom Metadata & Keyword Rules Form */}
        <PromptRules initialRules={rules} onRulesUpdated={setRulesState} />

        {/* Queue controls */}
        <QueueControls
          queueStatus={queueStatus}
          onStart={async () => { await startQueue(); await poll(); }}
          onPause={async () => { await pauseQueue(); await poll(); }}
          onStop={async () => { await stopQueue(); await poll(); }}
          onReset={async () => { await resetQueue(); setJobs([]); setSelected([]); await poll(); }}
          onRetryFailed={async (ids) => { await retryFailed(ids); await poll(); }}
        />

        {/* Drop zone */}
        <div
          onDragOver={e => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={e => { e.preventDefault(); setIsDragging(false); }}
          onDrop={handleDrop}
          onClick={() => document.getElementById('file-input').click()}
          style={{
            border:`2px dashed ${isDragging ? 'var(--accent)' : 'var(--border-strong)'}`,
            borderRadius:'var(--radius-lg)', padding:'28px 20px', textAlign:'center',
            cursor:'pointer', background: isDragging ? 'var(--accent-light)' : 'var(--bg-surface)',
            transition:'all 0.15s', transform: isDragging ? 'scale(0.995)' : 'scale(1)'
          }}>
          <input type="file" id="file-input" multiple accept="image/*,video/*" className="hidden" onChange={e => handleFiles(e.target.files)}/>
          <UploadCloud size={32} style={{ color: isDragging ? 'var(--accent)' : 'var(--text-tertiary)', marginBottom:8 }}/>
          <p style={{ fontSize:14, fontWeight:600, color:'var(--text-secondary)', marginBottom:4 }}>
            {isDragging ? 'Drop files here' : 'Drag images & videos here'}
          </p>
          <p style={{ fontSize:12, color:'var(--text-tertiary)' }}>or click to browse · JPG, PNG, MP4, MOV and more</p>
        </div>

        {/* Filter bar */}
        {jobs.length > 0 && (
          <FilterBar
            jobs={jobs} filter={filter} sort={sort} selected={selected} allSelected={allSelected}
            onFilter={setFilter} onSort={setSort} onSelectAll={handleSelectAll}
            onDeleteSelected={handleDeleteSelected} onRetrySelected={handleRetrySelected}
          />
        )}

        {/* Jobs list */}
        <div style={{ display:'flex', flexDirection:'column', gap:10 }}>
          {jobs.length === 0 ? (
            <div style={{ textAlign:'center', padding:'48px 0', color:'var(--text-tertiary)', fontSize:13 }}>
              No files uploaded yet
            </div>
          ) : filteredJobs.length === 0 ? (
            <div style={{ textAlign:'center', padding:'32px 0', color:'var(--text-tertiary)', fontSize:13 }}>
              No files match this filter
            </div>
          ) : (
            filteredJobs.map((job, i) => (
              <FileRow
                key={job.id} job={{ ...job, fileObj: fileObjs[job.id] || null }}
                index={jobs.indexOf(job)} selected={selected.includes(job.id)}
                onSelect={id => setSelected(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id])}
                onDelete={handleJobDelete} onChange={handleJobChange} activePlatforms={platforms}
              />
            ))
          )}
        </div>
      </main>
    </div>
  );
}
