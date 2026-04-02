import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { projectAPI, profileAPI } from '../../services/api';
import Button from '../Common/Button';
import LoadingAnimation from '../Common/LoadingAnimation';
import FormField from '../Common/primitives/FormField';
import palette from '../../palette';

const P = palette;
const gold = P.colors.primary.cyan;
const txt = P.colors.text.primary;
const txt2 = P.colors.text.secondary;
const bdr2 = P.colors.border.secondary;
const mono = P.typography.fontFamily.primary;

const IdeaSubmission = ({ user, onSubmit }) => {
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    required_skills: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [rewriting, setRewriting] = useState(false);
  const [activeStyle, setActiveStyle] = useState(null);
  const [showStyles, setShowStyles] = useState(false);
  const [recording, setRecording] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [playingAudio, setPlayingAudio] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (formData.description.length < 500) {
      setError('Description must be at least 500 characters');
      return;
    }
    setLoading(true);
    setSubmitting(true);
    try {
      const skillsArray = formData.required_skills.split(',').map(s => s.trim()).filter(Boolean);
      const response = await projectAPI.create({
        title: formData.title,
        description: formData.description,
        required_skills: skillsArray,
      });
      setTimeout(async () => {
        await onSubmit();
        navigate(`/matches/${response.data.project._id}`);
      }, 10000);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to submit project');
      setLoading(false);
      setSubmitting(false);
    }
  };

  // AI Rewrite
  const Ic = ({ d, size = 12 }) => <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d={d} /></svg>;
  const styles = [
    { key: 'professional', label: 'Professional', icon: <Ic d="M20 7h-9M14 17H5M17 17a2 2 0 1 0 4 0 2 2 0 0 0-4 0zM3 7a2 2 0 1 0 4 0 2 2 0 0 0-4 0z" /> },
    { key: 'shorten', label: 'Shorten', icon: <Ic d="M6 9l6 6 6-6" /> },
    { key: 'elevator_pitch', label: 'Elevator Pitch', icon: <Ic d="M13 2L3 14h9l-1 8 10-12h-9l1-8z" /> },
    { key: 'formal', label: 'Formal', icon: <Ic d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6" /> },
    { key: 'casual', label: 'Casual', icon: <Ic d="M18 8h1a4 4 0 0 1 0 8h-1M2 8h16v9a4 4 0 0 1-4 4H6a4 4 0 0 1-4-4V8zM6 1v3M10 1v3M14 1v3" /> },
    { key: 'lengthy', label: 'Expand', icon: <Ic d="M15 3h6v6M9 21H3v-6M21 3l-7 7M3 21l7-7" /> },
    { key: 'storytelling', label: 'Story', icon: <Ic d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M4 19.5V5a2 2 0 0 1 2-2h14v14H6.5A2.5 2.5 0 0 0 4 19.5z" /> },
    { key: 'technical', label: 'Technical', icon: <Ic d="M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" /> },
  ];

  const handleRewrite = async (style) => {
    if (!formData.description.trim()) return;
    setRewriting(true); setActiveStyle(style);
    try {
      const res = await profileAPI.rewriteText({ text: formData.description, style });
      const rewritten = res.data?.rewritten || res.data?.details?.rewritten;
      if (rewritten) setFormData(p => ({ ...p, description: rewritten }));
    } catch (e) { console.error('Rewrite failed:', e); }
    finally { setRewriting(false); setActiveStyle(null); }
  };

  // Voice recording
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks = [];
      mr.ondataavailable = (e) => chunks.push(e.data);
      mr.onstop = async () => {
        stream.getTracks().forEach(t => t.stop());
        const blob = new Blob(chunks, { type: 'audio/webm' });
        try {
          const res = await profileAPI.speechToText(blob);
          const text = res.data?.text || res.data?.details?.text;
          if (text) setFormData(p => ({ ...p, description: p.description ? p.description + ' ' + text : text }));
        } catch (e) { console.error('STT failed:', e); }
      };
      mr.start();
      setMediaRecorder(mr); setRecording(true);
    } catch (e) { console.error('Mic access denied:', e); }
  };
  const stopRecording = () => { if (mediaRecorder) { mediaRecorder.stop(); setRecording(false); } };

  // TTS
  const handlePlayTTS = async () => {
    if (!formData.description.trim()) return;
    setPlayingAudio(true);
    try {
      const res = await profileAPI.textToSpeech(formData.description.slice(0, 4000), 'nova');
      const blob = new Blob([res.data], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => { setPlayingAudio(false); URL.revokeObjectURL(url); };
      audio.play();
    } catch (e) { console.error('TTS failed:', e); setPlayingAudio(false); }
  };

  const chipStyle = (active) => ({
    padding: '4px 10px', borderRadius: 999, border: `1px solid ${active ? gold : bdr2}`,
    background: active ? `${gold}18` : 'transparent', color: active ? gold : txt2,
    fontSize: 11, fontFamily: mono, cursor: rewriting ? 'wait' : 'pointer',
    letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center', gap: 4,
    transition: 'all 0.2s', opacity: rewriting && !active ? 0.5 : 1,
  });

  if (submitting) {
    return (
      <div style={{ maxWidth: '560px', margin: '0 auto', padding: P.spacing['2xl'] }}>
        <LoadingAnimation message="Reviewing your vision and calibrating fit models." duration={10000} />
      </div>
    );
  }

  const inputStyle = {
    width: '100%', padding: `${P.spacing.sm} 0`, backgroundColor: 'transparent',
    border: 'none', borderBottom: '1px solid #333333', color: txt,
    fontSize: P.typography.fontSize.base, outline: 'none',
    transition: `border-color ${P.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1), box-shadow ${P.transitions.normal} cubic-bezier(0.16, 1, 0.3, 1)`,
  };
  const focusProps = {
    onFocus: (e) => { e.target.style.borderBottomColor = gold; e.target.style.boxShadow = `0 2px 0 ${gold}`; },
    onBlur: (e) => { e.target.style.borderBottomColor = '#333333'; e.target.style.boxShadow = 'none'; },
  };

  return (
    <div style={{ maxWidth: '560px', margin: '0 auto', padding: P.spacing['2xl'] }}>
      <p className="mono-label" style={{ marginBottom: P.spacing.md }}>Founder Submission</p>
      <h1 style={{ fontFamily: P.typography.fontFamily.display, fontSize: P.typography.fontSize['4xl'], marginBottom: P.spacing.md }}>
        Submit Your Startup Vision
      </h1>
      <p style={{ color: txt2, marginBottom: P.spacing.xl }}>
        Build the brief that drives your match pipeline.
      </p>
      <div style={{ marginBottom: P.spacing.xl, height: '1px', backgroundColor: P.colors.border.primary, transform: 'scaleX(0)' }} className="rule-draw" />

      {error && (
        <div style={{ backgroundColor: 'rgba(216, 107, 107, 0.08)', border: `1px solid ${P.colors.status.error}`, color: P.colors.status.error, padding: P.spacing.md, borderRadius: P.borderRadius.md, marginBottom: P.spacing.lg, fontSize: P.typography.fontSize.sm }}>
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{ display: 'grid', gap: P.spacing.xl }}>
        <FormField label="Project Title *">
          <input type="text" name="title" value={formData.title} onChange={handleChange} required style={inputStyle} {...focusProps} />
        </FormField>

        <FormField label="Project Description * (minimum 500 characters)" hint={`${formData.description.length} / 500 characters`}>
          {/* AI + Voice toolbar */}
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8 }}>
            <button type="button" onClick={recording ? stopRecording : startRecording}
              style={{ ...chipStyle(recording), background: recording ? '#d86b6b22' : 'transparent', color: recording ? '#d86b6b' : txt2, border: `1px solid ${recording ? '#d86b6b' : bdr2}` }}>
              {recording
                ? <><svg width="10" height="10" viewBox="0 0 24 24" fill="currentColor"><rect x="4" y="4" width="16" height="16" rx="2"/></svg> Stop</>
                : <><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg> Voice</>
              }
            </button>
            {formData.description.trim() && (
              <button type="button" onClick={handlePlayTTS} disabled={playingAudio} style={chipStyle(playingAudio)}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"/></svg>
                {playingAudio ? ' Playing...' : ' Listen'}
              </button>
            )}
            <button type="button" onClick={() => setShowStyles(p => !p)}
              style={{ ...chipStyle(showStyles), background: showStyles ? `${gold}18` : 'transparent', color: showStyles ? gold : txt2 }}>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> AI Rewrite
            </button>
          </div>
          {showStyles && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
              {styles.map(s => (
                <button key={s.key} type="button" onClick={() => handleRewrite(s.key)}
                  disabled={rewriting || !formData.description.trim()} style={chipStyle(activeStyle === s.key)}>
                  {activeStyle === s.key ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> : s.icon} {s.label}
                </button>
              ))}
            </div>
          )}
          {rewriting && <p style={{ fontSize: 11, color: gold, marginBottom: 6, display: 'flex', alignItems: 'center', gap: 4 }}><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Rewriting as {activeStyle?.replace('_', ' ')}...</p>}
          <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
          <textarea
            name="description" value={formData.description} onChange={handleChange} required rows={12}
            placeholder="Describe your startup vision. You can type or use  Voice to speak. Use AI Rewrite to enhance your description."
            style={{ ...inputStyle, resize: 'vertical', fontFamily: mono }} {...focusProps}
          />
        </FormField>

        <FormField label="Required Skills (comma-separated)">
          <input type="text" name="required_skills" value={formData.required_skills} onChange={handleChange} style={inputStyle} {...focusProps} />
        </FormField>

        <div style={{ display: 'flex', gap: P.spacing.md, justifyContent: 'flex-end' }}>
          <Button type="button" variant="secondary" onClick={() => navigate('/dashboard')}>Cancel</Button>
          <Button type="submit" loading={loading}>{loading ? 'Submitting...' : 'Submit for Review'}</Button>
        </div>
      </form>
    </div>
  );
};

export default IdeaSubmission;
