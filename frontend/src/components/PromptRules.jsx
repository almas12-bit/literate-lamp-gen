import { useState, useEffect } from 'react';
import { Sliders, ShieldAlert, CheckCircle2, Sparkles, ChevronDown, ChevronUp, RotateCcw, Check } from 'lucide-react';
import { getRules, setRules } from '../api';

const MANDATORY_PRESETS = [
  { label: '+ Alpha / Transparent', words: 'alpha channel, transparent background, isolated' },
  { label: '+ Isolated on White', words: 'isolated on white, white background, cut out' },
  { label: '+ Green Screen', words: 'green screen, chroma key' },
  { label: '+ Seamless Loop', words: 'seamless loop, looping' }
];

const FORBIDDEN_PRESETS = [
  { label: '+ No 3D Render', words: 'rendering, 3d render, octane render, blender' },
  { label: '+ No Trademarks', words: 'apple, nike, sony, canon, nikon' },
  { label: '+ No 4K/HD Buzzwords', words: '4k, 8k, hd, wallpaper, masterpiece' }
];

const DEFAULT_FORBIDDEN = 'rendering, 3d render, octane render, blender, 4k';

export default function PromptRules({ initialRules, onRulesUpdated }) {
  const [isOpen, setIsOpen] = useState(false);
  const [mandatory, setMandatory] = useState('');
  const [forbidden, setForbidden] = useState(DEFAULT_FORBIDDEN);
  const [customInst, setCustomInst] = useState('');
  const [savedStatus, setSavedStatus] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (initialRules) {
      setMandatory(initialRules.mandatory_keywords || '');
      setForbidden(initialRules.forbidden_words !== undefined ? initialRules.forbidden_words : DEFAULT_FORBIDDEN);
      setCustomInst(initialRules.custom_instruction || '');
    } else {
      getRules().then(res => {
        if (res.data) {
          setMandatory(res.data.mandatory_keywords || '');
          setForbidden(res.data.forbidden_words !== undefined ? res.data.forbidden_words : DEFAULT_FORBIDDEN);
          setCustomInst(res.data.custom_instruction || '');
        }
      }).catch(() => {});
    }
  }, [initialRules]);

  const addPreset = (currentVal, setter, presetWords) => {
    const existing = currentVal ? currentVal.split(',').map(s => s.trim().toLowerCase()) : [];
    const newItems = presetWords.split(',').map(s => s.trim().toLowerCase());
    const combined = [...existing];
    for (const item of newItems) {
      if (!combined.includes(item)) combined.push(item);
    }
    const result = combined.filter(Boolean).join(', ');
    setter(result);
  };

  const handleSave = async (m = mandatory, f = forbidden, c = customInst) => {
    setSaving(true);
    try {
      const payload = {
        mandatory_keywords: m,
        forbidden_words: f,
        custom_instruction: c
      };
      await setRules(payload);
      setSavedStatus(true);
      if (onRulesUpdated) onRulesUpdated(payload);
      setTimeout(() => setSavedStatus(false), 2000);
    } catch (e) {
      console.error('Failed to save rules:', e);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setMandatory('');
    setForbidden(DEFAULT_FORBIDDEN);
    setCustomInst('');
    await handleSave('', DEFAULT_FORBIDDEN, '');
  };

  // Count active rules for the pill badge
  const activeCount = [
    mandatory.trim() ? 'Mandatory' : null,
    forbidden.trim() ? 'Forbidden' : null,
    customInst.trim() ? 'Instruction' : null
  ].filter(Boolean).length;

  return (
    <div className="card" style={{ padding: 0, overflow: 'hidden', border: '1px solid var(--border)' }}>
      {/* Header bar / Toggle */}
      <div 
        onClick={() => setIsOpen(prev => !prev)}
        style={{
          padding: '12px 16px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          cursor: 'pointer',
          background: 'var(--bg-surface-2)',
          userSelect: 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 'var(--radius)',
            background: activeCount > 0 ? 'rgba(79, 70, 229, 0.12)' : 'var(--bg-surface-3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Sliders size={15} style={{ color: activeCount > 0 ? 'var(--accent)' : 'var(--text-tertiary)' }} />
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
              <span>Metadata & Keyword Rules (Custom AI Form)</span>
              {activeCount > 0 ? (
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: '1px 7px', borderRadius: 10,
                  background: 'var(--accent)', color: 'white'
                }}>
                  {activeCount} Active
                </span>
              ) : (
                <span style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>Default</span>
              )}
            </div>
            <div style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>
              Sesuaikan kata wajib ada (alpha/transparan), kata dilarang (rendering), dan instruksi khusus
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {savedStatus && (
            <span style={{ fontSize: 11, color: 'var(--success)', display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600 }}>
              <Check size={13} /> Saved
            </span>
          )}
          <button 
            type="button" 
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--text-secondary)' }}
          >
            {isOpen ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
          </button>
        </div>
      </div>

      {/* Collapsible Form Body */}
      {isOpen && (
        <div style={{ padding: '16px 18px', display: 'flex', flexDirection: 'column', gap: 16, background: 'var(--bg-surface)' }}>
          
          {/* Section 1: Mandatory Keywords */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <CheckCircle2 size={14} style={{ color: 'var(--success)' }} />
                Kata yang WAJIB Ada (Mandatory Keywords)
              </label>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Diprioritaskan di awal & dijamin muncul</span>
            </div>
            <input 
              type="text"
              value={mandatory}
              onChange={e => setMandatory(e.target.value)}
              placeholder="Contoh: alpha channel, transparent background, isolated"
              style={{
                width: '100%', padding: '7px 10px', fontSize: 12,
                border: '1px solid var(--border)', borderRadius: 'var(--radius)',
                background: 'var(--bg-surface-2)', color: 'var(--text-primary)'
              }}
            />
            {/* Quick chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
              {MANDATORY_PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => addPreset(mandatory, setMandatory, p.words)}
                  style={{
                    fontSize: 10, padding: '3px 8px', borderRadius: 'var(--radius)',
                    border: '1px solid var(--border)', background: 'var(--bg-surface-2)',
                    color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 500
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--success)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                >
                  {p.label}
                </button>
              ))}
              {mandatory && (
                <button
                  type="button"
                  onClick={() => setMandatory('')}
                  style={{ fontSize: 10, padding: '3px 6px', color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Section 2: Forbidden Words */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <ShieldAlert size={14} style={{ color: 'var(--error)' }} />
                Kata yang DILARANG (Forbidden Words)
              </label>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Otomatis dicegah & disaring dari Title & Keywords</span>
            </div>
            <input 
              type="text"
              value={forbidden}
              onChange={e => setForbidden(e.target.value)}
              placeholder="Contoh: rendering, 3d render, octane render, blender, 4k"
              style={{
                width: '100%', padding: '7px 10px', fontSize: 12,
                border: '1px solid var(--border)', borderRadius: 'var(--radius)',
                background: 'var(--bg-surface-2)', color: 'var(--text-primary)'
              }}
            />
            {/* Quick chips */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 6 }}>
              {FORBIDDEN_PRESETS.map((p, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => addPreset(forbidden, setForbidden, p.words)}
                  style={{
                    fontSize: 10, padding: '3px 8px', borderRadius: 'var(--radius)',
                    border: '1px solid var(--border)', background: 'var(--bg-surface-2)',
                    color: 'var(--text-secondary)', cursor: 'pointer', fontWeight: 500
                  }}
                  onMouseEnter={e => e.currentTarget.style.borderColor = 'var(--error)'}
                  onMouseLeave={e => e.currentTarget.style.borderColor = 'var(--border)'}
                >
                  {p.label}
                </button>
              ))}
              {forbidden && (
                <button
                  type="button"
                  onClick={() => setForbidden('')}
                  style={{ fontSize: 10, padding: '3px 6px', color: 'var(--text-tertiary)', background: 'none', border: 'none', cursor: 'pointer' }}
                >
                  Clear
                </button>
              )}
            </div>
          </div>

          {/* Section 3: Custom Instructions */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 5 }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Sparkles size={14} style={{ color: 'var(--accent)' }} />
                Instruksi Tambahan (Custom Instruction - Opsional)
              </label>
              <span style={{ fontSize: 11, color: 'var(--text-tertiary)' }}>Gaya visual / arahan khusus ke Gemini AI</span>
            </div>
            <textarea
              rows={2}
              value={customInst}
              onChange={e => setCustomInst(e.target.value)}
              placeholder="Contoh: Jika gambar bergaya 3D, selalu sebut sebagai '3D illustration'. Fokuskan pada pencahayaan dan konsep modern."
              style={{
                width: '100%', padding: '7px 10px', fontSize: 12, resize: 'vertical',
                border: '1px solid var(--border)', borderRadius: 'var(--radius)',
                background: 'var(--bg-surface-2)', color: 'var(--text-primary)', lineHeight: 1.4
              }}
            />
          </div>

          {/* Action buttons */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid var(--border)' }}>
            <button
              type="button"
              onClick={handleReset}
              className="btn btn-secondary btn-xs"
              style={{ display: 'flex', alignItems: 'center', gap: 5 }}
            >
              <RotateCcw size={11} /> Reset ke Default
            </button>

            <button
              type="button"
              onClick={() => handleSave()}
              disabled={saving}
              className="btn btn-primary btn-sm"
              style={{ display: 'flex', alignItems: 'center', gap: 6 }}
            >
              <Check size={13} /> {saving ? 'Menyimpan…' : 'Simpan Aturan'}
            </button>
          </div>

        </div>
      )}
    </div>
  );
}
