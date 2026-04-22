import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { profileAPI } from '../../services/api';
import Button from '../Common/Button';
import palette from '../../palette';

const API = 'http://localhost:5001';
const P = palette;
const gold = P.colors.primary.cyan;
const bg0 = P.colors.background.primary;
const bg1 = P.colors.background.secondary;
const bg2 = P.colors.background.tertiary;
const txt = P.colors.text.primary;
const txt2 = P.colors.text.secondary;
const bdr = P.colors.border.primary;
const bdr2 = P.colors.border.secondary;
const errColor = P.colors.status.error;
const mono = P.typography.fontFamily.primary;
const listFields = new Set(['skills', 'tools', 'languages', 'coreDomains', 'interests']);

const inputStyle = { width: '100%', padding: '0.7rem 0.9rem', background: bg1, border: `1px solid ${bdr2}`, borderRadius: P.borderRadius.md, color: txt, fontSize: P.typography.fontSize.sm, fontFamily: mono, boxSizing: 'border-box', outline: 'none' };
const labelStyle = { display: 'block', fontSize: P.typography.fontSize.xs, letterSpacing: '0.12em', textTransform: 'uppercase', color: txt2, marginBottom: '0.45rem', fontFamily: mono };

const splitList = (v) => Array.isArray(v) ? v.map(String).map((x) => x.trim()).filter(Boolean) : (typeof v === 'string' ? v.split(',').map((x) => x.trim()).filter(Boolean) : []);
const blank = (v) => v === null || v === undefined || v === false || (typeof v === 'string' && !v.trim()) || (Array.isArray(v) && v.length === 0);
const normUrl = (v) => String(v || '').trim().replace(/\/+$/, '').toLowerCase();
const deriveNames = (u = {}) => {
  if (u.firstName || u.lastName) return { firstName: u.firstName || '', lastName: u.lastName || '' };
  const p = String(u.name || '').trim().split(/\s+/).filter(Boolean);
  return { firstName: p[0] || '', lastName: p.slice(1).join(' ') };
};
const buildInitialForm = (u = {}) => {
  const n = deriveNames(u);
  return {
    name: u.name || '', bio: u.bio || '', linkedin: u.linkedin || '', professional_title: u.professional_title || '', experience_years: u.experience_years || '', location: u.location || '',
    firstName: n.firstName, lastName: n.lastName, headline: u.headline || '', currentPosition: u.currentPosition || '', currentCompany: u.currentCompany || '', city: u.city || '', state: u.state || '', country: u.country || '',
    email: u.email || '', phone: u.phone || '', linkedinUrl: u.linkedinUrl || '', github: u.github || '', about: u.about || '', totalYearsExperience: u.totalYearsExperience || '',
    skills: Array.isArray(u.skills) ? u.skills.join(', ') : (u.skills || ''), tools: Array.isArray(u.tools) ? u.tools.join(', ') : (u.tools || ''), languages: Array.isArray(u.languages) ? u.languages.join(', ') : (u.languages || ''),
    coreDomains: Array.isArray(u.coreDomains) ? u.coreDomains.join(', ') : (u.coreDomains || ''), interests: Array.isArray(u.interests) ? u.interests.join(', ') : (u.interests || ''),
    aboutMe: u.aboutMe || '',
    industryInclination: u.industryInclination || '', skillStrength: u.skillStrength || '', careerGoals: u.careerGoals || '', preferredRole: u.preferredRole || '', preferredIndustry: u.preferredIndustry || '', strengths: u.strengths || '', weaknesses: u.weaknesses || '', workStyle: u.workStyle || '', hobbies: u.hobbies || '', openToWork: Boolean(u.openToWork),
  };
};
const mergeProfile = (cur, inc = {}) => {
  const m = { ...cur };
  Object.entries(inc).forEach(([k, v]) => {
    if (v === undefined || v === null) return;
    m[k] = listFields.has(k) ? Array.from(new Set(splitList(v))).join(', ') : v;
  });
  m.name = m.name || [m.firstName, m.lastName].filter(Boolean).join(' ');
  m.bio = m.bio || m.about || '';
  m.about = m.about || m.bio || '';
  m.linkedin = m.linkedin || m.linkedinUrl || '';
  m.linkedinUrl = m.linkedinUrl || m.linkedin || '';
  m.professional_title = m.professional_title || m.headline || '';
  m.location = m.location || [m.city, m.state, m.country].filter(Boolean).join(', ');
  m.totalYearsExperience = String(m.totalYearsExperience || m.experience_years || '');
  return m;
};
const statusBanner = (color, bgc, border) => ({ padding: '0.75rem 1rem', marginBottom: '1rem', border, borderRadius: P.borderRadius.md, color, background: bgc, fontSize: P.typography.fontSize.sm });
const grid = (cols = 2) => ({ display: 'grid', gridTemplateColumns: `repeat(auto-fit, minmax(${cols === 3 ? 160 : 220}px, 1fr))`, gap: '0 1rem' });

const Field = ({ text, children }) => <div style={{ marginBottom: '1.15rem' }}><label style={labelStyle}>{text}</label>{children}</div>;

const LinkedInIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/></svg>
);

/* ─── Typeform-style Chatbot Overlay ─── */
function TypeformChat({ messages, chatInput, setChatInput, onSend, loading, extraCount, onClose, completed }) {
  const chatEndRef = useRef(null);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
  const inputDisabled = loading || completed;
  return (
    <div style={{
      position: 'fixed', bottom: 0, right: 0, zIndex: 8888,
      width: '100%', maxWidth: 460, height: '70vh', maxHeight: 640,
      display: 'flex', flexDirection: 'column',
      background: bg0, border: `1px solid ${bdr}`, borderRadius: '20px 20px 0 0',
      boxShadow: '0 -8px 40px rgba(0,0,0,0.5)',
      animation: 'slideUp 0.4s ease-out',
    }}>
      <style>{`@keyframes slideUp { from { transform: translateY(100%); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
        @keyframes fieldPop { from { transform: scale(0.8); opacity: 0; } to { transform: scale(1); opacity: 1; } }`}</style>
      <div style={{ padding: '1rem 1.25rem', background: `linear-gradient(135deg, ${gold}18, ${bg2})`, borderBottom: `1px solid ${bdr}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '20px 20px 0 0' }}>
        <div>
          <div style={{ fontSize: P.typography.fontSize.xs, letterSpacing: '0.12em', textTransform: 'uppercase', color: gold, fontFamily: mono }}>
            {completed ? 'Interview Complete' : 'Founder Profiling'}
          </div>
          <div style={{ fontSize: P.typography.fontSize.sm, color: txt2, marginTop: 2 }}>
            {completed
              ? 'Profile is ready — close this to review your About Me.'
              : (extraCount > 0 ? `${extraCount} insight${extraCount === 1 ? '' : 's'} collected` : 'Building your founder profile...')}
          </div>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: txt2, cursor: 'pointer', fontSize: 18, padding: 4 }} title={completed ? 'Close' : 'Minimize'}>&#x2715;</button>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {messages.map((m, i) => (
          <div key={`${m.role}-${i}`} style={{
            alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start',
            maxWidth: '85%', padding: '0.85rem 1rem',
            borderRadius: m.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
            background: m.role === 'user' ? `${gold}1f` : bg2,
            border: `1px solid ${m.role === 'user' ? `${gold}55` : bdr}`,
            fontSize: P.typography.fontSize.sm, color: txt, lineHeight: 1.65,
            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
            animation: 'fieldPop 0.3s ease-out',
          }}>{m.text}</div>
        ))}
        {loading && <div style={{ alignSelf: 'flex-start', padding: '0.85rem 1rem', borderRadius: '18px 18px 18px 4px', background: bg2, border: `1px solid ${bdr}`, color: txt2, fontSize: P.typography.fontSize.sm }}>
          <span style={{ animation: 'pulse 1.2s infinite', display: 'inline-block' }}>Thinking...</span>
        </div>}
        <div ref={chatEndRef} />
      </div>

      <div style={{ padding: '0.75rem 1rem 1rem', borderTop: `1px solid ${bdr}`, display: 'flex', gap: '0.5rem', background: bg0 }}>
        <input
          type="text" value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey && !inputDisabled) { e.preventDefault(); onSend(); } }}
          placeholder={completed ? 'Interview complete — thanks!' : 'Type your answer...'}
          disabled={inputDisabled}
          style={{
            ...inputStyle, flex: 1, minHeight: 46, borderRadius: '24px', paddingLeft: '1.1rem',
            opacity: inputDisabled ? 0.5 : 1,
            cursor: inputDisabled ? 'not-allowed' : 'text',
          }}
        />
        <button onClick={onSend} disabled={inputDisabled || !chatInput.trim()} style={{
          width: 46, height: 46, borderRadius: '50%', border: 'none',
          background: (chatInput.trim() && !inputDisabled) ? gold : bdr2, color: bg0,
          cursor: (chatInput.trim() && !inputDisabled) ? 'pointer' : 'not-allowed', fontSize: 18,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'background 0.2s',
          opacity: inputDisabled ? 0.5 : 1,
        }}>&#x2191;</button>
      </div>
    </div>
  );
}

/* ─── Dynamic Field Card (animated, auto-textarea for long values) ─── */
function DynamicFieldCard({ label: fieldLabel, value, onChange, isNew }) {
  const displayValue = Array.isArray(value) ? value.join(', ') : String(value || '');
  const isLong = displayValue.length > 50 || displayValue.includes(',');
  const filledStyle = { ...inputStyle, fontSize: '0.92rem', color: displayValue ? txt : txt2 };
  return (
    <div style={{ animation: isNew ? 'fieldPop 0.5s ease-out' : 'none', marginBottom: '0.25rem' }}>
      <Field text={fieldLabel}>
        {isLong ? (
          <textarea value={displayValue} onChange={onChange} placeholder="Not answered yet..." style={{ ...filledStyle, minHeight: 60, resize: 'vertical' }} />
        ) : (
          <input value={displayValue} onChange={onChange} placeholder="Not answered yet..." style={filledStyle} title={displayValue} />
        )}
      </Field>
    </div>
  );
}


/* ─── About Me with AI Enhancer (no voice; auto-filled by chatbot wrap-up) ─── */
function AboutMeEditor({ value, onChange }) {
  const [rewriting, setRewriting] = useState(false);
  const [activeStyle, setActiveStyle] = useState(null);
  const [showStyles, setShowStyles] = useState(false);

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
    if (!value.trim()) return;
    setRewriting(true); setActiveStyle(style);
    try {
      const res = await profileAPI.rewriteText({ text: value, style });
      const rewritten = res.data?.rewritten || res.data?.details?.rewritten;
      if (rewritten) onChange(rewritten);
    } catch (e) {
      console.error('Rewrite failed:', e);
    } finally {
      setRewriting(false); setActiveStyle(null);
    }
  };

  const chipStyle = (active) => ({
    padding: '4px 10px', borderRadius: 999, border: `1px solid ${active ? gold : bdr2}`,
    background: active ? `${gold}18` : 'transparent', color: active ? gold : txt2,
    fontSize: 11, fontFamily: mono, cursor: rewriting ? 'wait' : 'pointer',
    letterSpacing: '0.04em', display: 'inline-flex', alignItems: 'center', gap: 4,
    transition: 'all 0.2s', opacity: rewriting && !active ? 0.5 : 1,
  });

  return (
    <div style={{ marginBottom: '1.15rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.45rem' }}>
        <label style={labelStyle}>About Me</label>
        <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
          <button type="button" onClick={() => setShowStyles(p => !p)}
            style={{ ...chipStyle(showStyles), background: showStyles ? `${gold}18` : 'transparent', color: showStyles ? gold : txt2 }}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/></svg> AI Rewrite
          </button>
        </div>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="The AI will write a crisp About Me for you once the chatbot interview completes. You can edit it any time, or use AI Rewrite to change the tone."
        style={{ ...inputStyle, minHeight: 100, resize: 'vertical', fontSize: '0.92rem', lineHeight: 1.7 }}
      />
      {showStyles && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 8, animation: 'fieldPop 0.2s ease-out' }}>
          {styles.map(s => (
            <button key={s.key} type="button" onClick={() => handleRewrite(s.key)}
              disabled={rewriting || !value.trim()}
              style={chipStyle(activeStyle === s.key)}>
              {activeStyle === s.key ? <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> : s.icon} {s.label}
            </button>
          ))}
        </div>
      )}
      {rewriting && <p style={{ fontSize: 11, color: gold, marginTop: 6, display: 'flex', alignItems: 'center', gap: 4 }}><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Rewriting as {activeStyle?.replace('_', ' ')}...</p>}
      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

export default function ProfileEdit({ user, onUpdate }) {
  const initialForm = useMemo(() => buildInitialForm(user), [user]);
  const [formData, setFormData] = useState(initialForm);
  const [resume, setResume] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploadingResume, setUploadingResume] = useState(false);
  const [downloadingResume, setDownloadingResume] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [vectorStatus, setVectorStatus] = useState('');
  const [resumeAnalysis, setResumeAnalysis] = useState(null);
  const [linkedinUrlInput, setLinkedinUrlInput] = useState(user.linkedinUrl || user.linkedin || '');
  const [activeScrapeUrl, setActiveScrapeUrl] = useState(normUrl(user.linkedinUrl || user.linkedin || ''));
  const [isScraping, setIsScraping] = useState(false);
  const [postsScraped, setPostsScraped] = useState(0);
  const [scrapeCooldown, setScrapeCooldown] = useState(0);

  // Typeform chatbot — chat thread is hydrated from the persisted user.chatHistory
  // so a hard refresh restores the exact thread, not a fresh greeting.
  const [showChatbot, setShowChatbot] = useState(false);
  const [chatMessages, setChatMessages] = useState(() => Array.isArray(user.chatHistory) ? user.chatHistory : []);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [conversationDone, setConversationDone] = useState(() => Number(user.profileConfidenceScore || 0) >= 80);

  // Dynamic fields — chatbot Q&A goes straight to Mongo (no per-turn UI panel),
  // so we only track scrape-discovered insights here for the "Discovered" panel.
  const [extraFields, setExtraFields] = useState(user.extraFields || {});
  const [dynamicFieldLabels, setDynamicFieldLabels] = useState(user.dynamicFieldLabels || {});
  const [discoveredFields, setDiscoveredFields] = useState(user.postInsights || {});
  const [linkedinFieldKeys, setLinkedinFieldKeys] = useState(() => new Set(user.linkedinFieldKeys || []));
  const [newFieldKeys, setNewFieldKeys] = useState(new Set());
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Re-hydrate when the parent passes a fresh user object (e.g., after Save).
  useEffect(() => {
    if (Array.isArray(user.chatHistory)) setChatMessages(user.chatHistory);
    if (Array.isArray(user.linkedinFieldKeys)) setLinkedinFieldKeys(new Set(user.linkedinFieldKeys));
    setConversationDone(Number(user.profileConfidenceScore || 0) >= 80);
  }, [user.chatHistory, user.linkedinFieldKeys, user.profileConfidenceScore]);

  useEffect(() => {
    const handler = (e) => { if (hasUnsavedChanges) { e.preventDefault(); e.returnValue = ''; } };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [hasUnsavedChanges]);

  const tok = () => localStorage.getItem('token');
  const toArr = (v) => Array.isArray(v) ? v : splitList(v);

  const handleScrape = async () => {
    if (!linkedinUrlInput.trim()) return setError('Please enter a LinkedIn URL');
    if (scrapeCooldown > 0) return setError(`Rate limit - wait ${scrapeCooldown}s`);
    setIsScraping(true);
    setError('');
    setSuccess('');
    try {
      const requestedUrl = normUrl(linkedinUrlInput);
      if (requestedUrl && requestedUrl !== activeScrapeUrl) {
        setFormData(initialForm);
        setExtraFields({});
        setDynamicFieldLabels({});
        setDiscoveredFields({});
        setChatMessages([]);
        setPostsScraped(0);
      }
      const res = await axios.post(
        `${API}/api/profile/scrape-linkedin`,
        { linkedinUrl: linkedinUrlInput },
        { headers: { Authorization: `Bearer ${tok()}` } }
      );
      const d = res.data.details;
      const { profileData, postsScraped: ps, aiStatus, deepPostInsights, extraFields: sExtra, dynamicFieldLabels: sLabels, linkedinFieldKeys: sLinkedinKeys, persisted } = d;
      setPostsScraped(ps || 0);
      // About Me is reserved for the AI summary generated at the end of the
      // chatbot interview. Keep those fields empty in the form even though
      // LinkedIn's bio was scraped.
      const scrapedForForm = { ...(profileData || {}) };
      delete scrapedForForm.about;
      delete scrapedForForm.aboutMe;
      delete scrapedForForm.bio;
      const merged = mergeProfile(buildInitialForm({}), scrapedForForm);
      merged.about = '';
      merged.aboutMe = '';
      merged.bio = '';
      setFormData(merged);
      setActiveScrapeUrl(normUrl(profileData?.linkedinUrl || linkedinUrlInput));
      if (deepPostInsights) setDiscoveredFields(deepPostInsights);
      if (sExtra) {
        setExtraFields(prev => {
          const m = { ...prev, ...sExtra };
          setNewFieldKeys(new Set(Object.keys(sExtra)));
          setTimeout(() => setNewFieldKeys(new Set()), 3000);
          return m;
        });
      }
      if (sLabels) setDynamicFieldLabels(prev => ({ ...prev, ...sLabels }));
      if (Array.isArray(sLinkedinKeys)) setLinkedinFieldKeys(new Set(sLinkedinKeys));
      // Backend now normalizes and saves before returning. No unsaved banner needed.
      setHasUnsavedChanges(false);
      setSuccess(
        `Profile auto-filled from LinkedIn${ps > 0 ? ` · ${ps} posts analyzed` : ''}` +
        `${aiStatus !== 'ok' ? ' (AI limited)' : ''}` +
        `${persisted ? ' · saved' : ' · NOT saved — retry'}`
      );
      // Refresh the parent user object so chatHistory/postInsights/etc. are fresh.
      if (persisted && typeof onUpdate === 'function') onUpdate();
      // Bootstrap the chatbot with the freshly persisted user state.
      setChatMessages([]);
      if (!conversationDone) {
        setShowChatbot(true);
        setChatLoading(true);
        try {
          const cr = await profileAPI.founderChat({ bootstrap: true });
          const cd = cr.data || {};
          const history = Array.isArray(cd.chatHistory) ? cd.chatHistory : [];
          if (history.length) setChatMessages(history);
          else if (cd.reply) setChatMessages([{ role: 'model', text: cd.reply }]);
          if (Array.isArray(cd.linkedinFieldKeys)) setLinkedinFieldKeys(new Set(cd.linkedinFieldKeys));
        } catch {
          setChatMessages([{ role: 'model', text: "Let's start. How many hours per week can you commit to a startup venture?" }]);
        } finally {
          setChatLoading(false);
        }
      }
    } catch (e) {
      const status = e.response?.status;
      if (status === 429) {
        let s = 60;
        setScrapeCooldown(s);
        const t = setInterval(() => {
          s--;
          setScrapeCooldown(s);
          if (s <= 0) clearInterval(t);
        }, 1000);
        setError(`Rate limited - wait ${s}s`);
      } else {
        setError(`Scraping failed: ${e.response?.data?.message || e.message}`);
      }
    } finally {
      setIsScraping(false);
    }
  };

  const handleChange = (e) => { const { name, value, type, checked } = e.target; setFormData(p => ({ ...p, [name]: type === 'checkbox' ? checked : value })); setHasUnsavedChanges(true); setError(''); };

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError(''); setSuccess(''); setVectorStatus('');
    try {
      // Save persists manual form edits. The chatbot already auto-saves its own
      // answers, so we don't need a separate chatbotFieldKeys list here.
      await profileAPI.updateProfile({
        ...formData,
        skills: toArr(formData.skills), tools: toArr(formData.tools), languages: toArr(formData.languages),
        coreDomains: toArr(formData.coreDomains), interests: toArr(formData.interests),
        experience_years: parseInt(formData.experience_years, 10) || parseInt(formData.totalYearsExperience, 10) || 0,
        extraFields,
        dynamicFieldLabels,
      });
      setHasUnsavedChanges(false); setSuccess('Profile saved.'); setVectorStatus('indexing');
      setTimeout(() => { setVectorStatus('done'); onUpdate(); }, 3500);
    } catch (e2) { setError(e2.response?.data?.error || 'Failed to save profile'); } finally { setLoading(false); }
  };

  const handleResumeChange = (e) => { const f = e.target.files?.[0]; if (!f) return; if (!['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(f.type)) return setError('Only PDF and DOCX'); if (f.size > 10 * 1024 * 1024) return setError('Max 10MB'); setResume(f); setError(''); };
  const handleResumeUpload = async () => { if (!resume) return setError('Select a file'); setUploadingResume(true); setError(''); setVectorStatus(''); try { const fd = new FormData(); fd.append('resume', resume); const res = await profileAPI.uploadResume(fd); setSuccess('Resume uploaded.'); setVectorStatus('indexing'); setResumeAnalysis(res.data.details?.analysis || null); setResume(null); if (res.data.details?.analysis?.merged_skills) setFormData(p => ({ ...p, skills: res.data.details.analysis.merged_skills.join(', ') })); setTimeout(() => { setVectorStatus('done'); onUpdate(); }, 3500); } catch (e) { setError(e.response?.data?.error || 'Upload failed'); } finally { setUploadingResume(false); } };
  const handleDownloadResume = async () => { setDownloadingResume(true); setError(''); try { const res = await profileAPI.getResume(user._id); const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/pdf' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = user.resume || 'resume.pdf'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url); } catch (e) { const d = e.response?.data; if (d instanceof Blob) { try { const t = JSON.parse(await d.text()); setError(t.error || 'Download failed'); } catch { setError('Download failed'); } } else setError(e.response?.data?.error || 'Download failed'); } finally { setDownloadingResume(false); } };
  const handleDeleteResume = async () => { if (!window.confirm('Delete your resume?')) return; try { await profileAPI.deleteResume(); setSuccess('Resume deleted.'); setVectorStatus('indexing'); setTimeout(() => { setVectorStatus('done'); onUpdate(); }, 3500); } catch (e) { setError(e.response?.data?.error || 'Delete failed'); } };

  const missingBasic = ['firstName', 'lastName', 'headline', 'email'].filter(f => blank(formData[f])).length;
  const extraFieldEntries = Object.entries(extraFields).filter(([k, v]) => v !== null && v !== undefined && v !== '' && !(Array.isArray(v) && v.length === 0) && linkedinFieldKeys.has(k));

  const handleChatSend = useCallback(async () => {
    const text = chatInput.trim();
    if (!text) return;
    // Interview is already complete — do not send further messages.
    if (conversationDone) return;
    // Optimistic append so the user's message renders immediately.
    setChatMessages(prev => [...prev, { role: 'user', text }]);
    setChatInput('');
    setChatLoading(true);
    try {
      const res = await profileAPI.founderChat({
        userMessage: text,
        isResumeMode: conversationDone,
      });
      const d = res.data || {};
      // Server returns the full persisted chatHistory — adopt it as truth.
      const history = Array.isArray(d.chatHistory) ? d.chatHistory : null;
      if (history) setChatMessages(history);
      else if (d.reply) setChatMessages(prev => [...prev, { role: 'model', text: d.reply }]);

      // Reflect any new top-level fields (e.g., extracted standard fields,
      // generated About Me) into the form so the user sees them immediately.
      const allExtra = d.allExtraFields;
      const allLabels = d.allFieldLabels;
      if (allExtra) setExtraFields(prev => ({ ...prev, ...allExtra }));
      if (allLabels) setDynamicFieldLabels(prev => ({ ...prev, ...allLabels }));
      if (Array.isArray(d.linkedinFieldKeys)) setLinkedinFieldKeys(new Set(d.linkedinFieldKeys));

      // Apply any enriched Basic Info fields the backend produced on
      // conversation completion (aboutMe, headline, strengths, workStyle,
      // careerGoals, preferredRole, preferredIndustry).
      const enriched = d.enrichedFields || {};
      if (enriched.aboutMe) {
        enriched.about = enriched.aboutMe;
      } else if (d.aboutMe) {
        enriched.aboutMe = d.aboutMe;
        enriched.about = d.aboutMe;
      }
      if (Object.keys(enriched).length > 0) {
        setFormData(prev => ({ ...prev, ...enriched }));
      }

      if (d.conversationComplete) {
        setConversationDone(true);
        // Pull in everything the backend just persisted.
        if (typeof onUpdate === 'function') onUpdate();
      }
    } catch (e) {
      setChatMessages(prev => [...prev, {
        role: 'model',
        text: e?.response?.status === 429 ? 'AI rate limited. Wait a moment.' : 'Something went wrong. Try again.',
      }]);
    } finally { setChatLoading(false); }
  }, [chatInput, conversationDone, onUpdate]);

  return <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '1.5rem', fontFamily: mono, color: txt, background: bg0 }}>

    {/* Typeform Chatbot */}
    {showChatbot && <TypeformChat messages={chatMessages} chatInput={chatInput} setChatInput={setChatInput} onSend={handleChatSend} loading={chatLoading} extraCount={extraFieldEntries.length} onClose={() => setShowChatbot(false)} completed={conversationDone} />}

    {/* Header */}
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
      <h2 style={{ fontFamily: P.typography.fontFamily.display, fontSize: P.typography.fontSize['2xl'], fontWeight: 300, color: txt, letterSpacing: '0.04em', margin: 0 }}>Edit Profile</h2>
    </div>

    {error && <div style={statusBanner(errColor, `${errColor}0d`, `1px solid ${errColor}44`)}>{error}</div>}
    {success && <div style={statusBanner(gold, `${gold}0d`, `1px solid ${gold}44`)}>{success}</div>}
    {vectorStatus === 'indexing' && <div style={statusBanner(txt2, `${bdr}22`, `1px solid ${bdr2}`)}>Updating talent index...</div>}
    {vectorStatus === 'done' && <div style={statusBanner(gold, `${gold}0d`, `1px solid ${gold}44`)}>Talent index updated.</div>}

    <form onSubmit={handleSubmit} autoComplete="off">

      <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden' }}>
        <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            <LinkedInIcon /> LinkedIn Scrape
          </span>
          <Button type="button" onClick={() => { setLinkedinUrlInput(''); setActiveScrapeUrl(''); }} variant="outline" size="sm">
            Clear URL
          </Button>
        </div>
        <div style={{ padding: '1.25rem' }}>
          <p style={{ fontSize: P.typography.fontSize.sm, color: txt2, marginBottom: '1rem', lineHeight: 1.6 }}>
            Paste your LinkedIn profile URL or username below. Scraping is handled by Apify in the backend, so no LinkedIn login is required.
          </p>
          <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ flex: 1, minWidth: 220, display: 'flex', alignItems: 'center', background: bg1, border: `1px solid ${bdr2}`, borderRadius: P.borderRadius.md, overflow: 'hidden' }}>
              <span style={{ padding: '0.7rem 0 0.7rem 0.9rem', color: txt2, fontSize: P.typography.fontSize.sm, fontFamily: mono, whiteSpace: 'nowrap', userSelect: 'none' }}>linkedin.com/in/</span>
              <input
                type="text"
                placeholder="your-username"
                value={linkedinUrlInput.replace(/^https?:\/\/(www\.)?linkedin\.com\/in\//i, '')}
                onChange={(e) => {
                  const val = e.target.value.replace(/\s/g, '').toLowerCase();
                  setLinkedinUrlInput(val ? `https://www.linkedin.com/in/${val}` : '');
                }}
                style={{ ...inputStyle, border: 'none', background: 'transparent', paddingLeft: 0, flex: 1 }}
              />
            </div>
            <Button type="button" onClick={handleScrape} disabled={isScraping || scrapeCooldown > 0 || !linkedinUrlInput.trim()} variant="primary" size="sm">
              {isScraping ? 'Scraping...' : !linkedinUrlInput.trim() ? 'Enter username' : 'Scrape & Auto-fill'}
            </Button>
          </div>
          <p style={{ fontSize: 10, color: txt2, marginTop: '0.5rem', fontStyle: 'italic' }}>
            Enter the exact LinkedIn username or profile URL. After scraping, the profile data is auto-filled as before.
          </p>
          {postsScraped > 0 && <p style={{ fontSize: 11, color: txt2, marginTop: '0.75rem' }}>{postsScraped} posts deeply analyzed.</p>}
        </div>
      </div>

      {/* Basic Info */}
      <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
        <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            Basic Info
            {missingBasic > 0 && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${gold}66`, color: gold, background: `${gold}18` }}>{missingBasic} missing</span>}
          </span>
        </div>
        <div style={{ padding: '1.25rem' }}>
          <div style={grid(2)}>
            <Field text="First Name"><input name="firstName" value={formData.firstName} onChange={handleChange} style={inputStyle} placeholder="John" /></Field>
            <Field text="Last Name"><input name="lastName" value={formData.lastName} onChange={handleChange} style={inputStyle} placeholder="Doe" /></Field>
          </div>
          <Field text="Professional Headline"><input name="headline" value={formData.headline} onChange={handleChange} style={inputStyle} placeholder="Senior ML Engineer" /></Field>
          <AboutMeEditor
            value={formData.aboutMe || formData.about}
            onChange={(val) => { setFormData(p => ({ ...p, about: val, aboutMe: val })); setHasUnsavedChanges(true); }}
          />
          <Field text="Email"><input name="email" value={formData.email} onChange={handleChange} style={inputStyle} type="email" placeholder="you@example.com" /></Field>
          <Field text="LinkedIn URL"><input name="linkedinUrl" value={formData.linkedinUrl} onChange={handleChange} style={inputStyle} placeholder="https://linkedin.com/in/..." /></Field>
          <div style={{ marginTop: '1rem', padding: '1rem', border: `1px solid ${bdr2}`, borderRadius: P.borderRadius.md }}>
            <p style={{ ...labelStyle, marginBottom: '0.8rem' }}>Resume (PDF / DOCX)</p>
            {user.resume && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.8rem', padding: '0.5rem 0.75rem', background: bg2, borderRadius: P.borderRadius.md, border: `1px solid ${bdr2}` }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke={gold} strokeWidth="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <span style={{ fontSize: P.typography.fontSize.sm, color: txt, flex: 1 }}>{resume ? resume.name : user.resume.replace(/^[a-f0-9]{24}_/, '')}</span>
                <span style={{ fontSize: 10, color: '#0a6', textTransform: 'uppercase', letterSpacing: '0.08em' }}>Uploaded</span>
              </div>
            )}
            <input type="file" accept=".pdf,.docx,.doc" onChange={handleResumeChange} style={{ fontSize: P.typography.fontSize.xs, color: txt2, marginBottom: '0.8rem', display: 'block' }} />
            <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
              <Button type="button" onClick={handleResumeUpload} disabled={uploadingResume || !resume} variant="primary" size="sm">{uploadingResume ? 'Uploading...' : 'Upload'}</Button>
              {user.resume && <><Button type="button" onClick={handleDownloadResume} disabled={downloadingResume} variant="secondary" size="sm">{downloadingResume ? 'Downloading...' : 'Download'}</Button><Button type="button" onClick={handleDeleteResume} variant="outline" size="sm">Delete</Button></>}
            </div>
            {resumeAnalysis?.merged_skills?.length > 0 && <p style={{ fontSize: 11, color: txt2, marginTop: '0.6rem' }}>Extracted: {resumeAnalysis.merged_skills.join(', ')}</p>}
          </div>
          <p style={{ fontSize: P.typography.fontSize.xs, color: txt2, marginTop: '1.5rem', padding: '0.75rem', background: `${gold}08`, border: `1px solid ${gold}22`, borderRadius: P.borderRadius.md, lineHeight: 1.6 }}>
            Everything else (skills, goals, founder preferences, etc.) is collected by the AI chatbot after LinkedIn scrape.
          </p>
        </div>
      </div>

      {/* Auto-filled from LinkedIn */}
      {(formData.skills || formData.about || formData.currentPosition) && (
        <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
          <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
            Auto-Filled from LinkedIn & AI
          </div>
          <div style={{ padding: '1.25rem' }}>
            {formData.about && <Field text="About"><textarea name="about" value={formData.about} onChange={handleChange} style={{ ...inputStyle, minHeight: 80, resize: 'vertical' }} /></Field>}
            <div style={grid(2)}>
              {formData.currentPosition && <Field text="Current Role"><input name="currentPosition" value={formData.currentPosition} onChange={handleChange} style={inputStyle} /></Field>}
              {formData.currentCompany && <Field text="Company"><input name="currentCompany" value={formData.currentCompany} onChange={handleChange} style={inputStyle} /></Field>}
            </div>
            {formData.skills && <Field text="Skills"><textarea name="skills" value={formData.skills} onChange={handleChange} style={{ ...inputStyle, minHeight: 60, resize: 'vertical' }} /></Field>}
            {formData.tools && <Field text="Tools"><textarea name="tools" value={formData.tools} onChange={handleChange} style={{ ...inputStyle, minHeight: 60, resize: 'vertical' }} /></Field>}
            <div style={grid(2)}>
              {formData.coreDomains && <Field text="Core Domains"><input name="coreDomains" value={formData.coreDomains} onChange={handleChange} style={inputStyle} /></Field>}
              {formData.interests && <Field text="Interests"><input name="interests" value={formData.interests} onChange={handleChange} style={inputStyle} /></Field>}
            </div>
            <div style={grid(2)}>
              {formData.totalYearsExperience && <Field text="Years of Experience"><input name="totalYearsExperience" value={formData.totalYearsExperience} onChange={handleChange} style={inputStyle} /></Field>}
              {formData.workStyle && <Field text="Work Style"><input name="workStyle" value={formData.workStyle} onChange={handleChange} style={inputStyle} /></Field>}
            </div>
          </div>
        </div>
      )}

      {/* Discovered from LinkedIn — scrape insights only.
          Chatbot Q&A is no longer surfaced here; it streams straight to Mongo
          and shows in the floating chatbot UI. */}
      {extraFieldEntries.length > 0 && (
        <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
          <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              Discovered from LinkedIn
              <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${bdr2}`, color: txt2 }}>{extraFieldEntries.length} insights</span>
            </span>
          </div>
          <div style={{ padding: '1.25rem' }}>
            <div style={grid(2)}>
              {extraFieldEntries.map(([key, value]) => {
                const fl = dynamicFieldLabels[key] || key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase()).trim();
                return (
                  <DynamicFieldCard key={key} label={fl} value={value} isNew={newFieldKeys.has(key)}
                    onChange={(e) => { setExtraFields(prev => ({ ...prev, [key]: e.target.value })); setHasUnsavedChanges(true); }} />
                );
              })}
            </div>
          </div>
        </div>
      )}

      {hasUnsavedChanges && <div style={statusBanner(gold, `${gold}0d`, `1px solid ${gold}44`)}>You have unsaved changes. Click Save to persist your profile to the database and enable matching.</div>}
      <Button type="submit" disabled={loading} variant="primary" size="lg" fullWidth>{loading ? 'Saving...' : hasUnsavedChanges ? 'Save Profile (unsaved changes)' : 'Save Profile'}</Button>
    </form>

    {/* Floating chat trigger — disabled once interview is complete. */}
    {!showChatbot && !conversationDone && (
      <button
        onClick={async () => {
          setShowChatbot(true);
          if (chatMessages.length === 0) {
            setChatLoading(true);
            try {
              const cr = await profileAPI.founderChat({ bootstrap: true });
              const cd = cr.data || {};
              const history = Array.isArray(cd.chatHistory) ? cd.chatHistory : [];
              if (history.length) setChatMessages(history);
              else if (cd.reply) setChatMessages([{ role: 'model', text: cd.reply }]);
              if (Array.isArray(cd.linkedinFieldKeys)) setLinkedinFieldKeys(new Set(cd.linkedinFieldKeys));
            } catch {
              setChatMessages([{ role: 'model', text: "Tell me about your startup ambitions to start the interview." }]);
            } finally { setChatLoading(false); }
          }
        }}
        style={{
          position: 'fixed', bottom: 24, right: 24, zIndex: 7777,
          width: 60, height: 60, borderRadius: '50%',
          background: `linear-gradient(135deg, ${gold}, ${gold}cc)`, border: 'none',
          color: bg0, fontSize: 26, cursor: 'pointer',
          boxShadow: `0 4px 20px ${gold}55`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'transform 0.2s',
        }}
        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        title="Open Founder Chat"
      >
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12a8.5 8.5 0 0 1-8.5 8.5H7l-4 3v-6.5A8.5 8.5 0 1 1 21 12Z" /><path d="M8 10h8" /><path d="M8 14h5" /></svg>
      </button>
    )}
  </div>;
}
