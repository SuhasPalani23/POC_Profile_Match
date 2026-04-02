import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import axios from 'axios';
import { profileAPI, linkedinAuthAPI } from '../../services/api';
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

/* ─── Consent Modal ─── */
function ConsentModal({ onAgree, onCancel }) {
  const [scrolledToBottom, setScrolledToBottom] = useState(false);
  const scrollRef = useRef(null);
  const handleScroll = () => {
    const el = scrollRef.current;
    if (el && el.scrollHeight - el.scrollTop - el.clientHeight < 30) setScrolledToBottom(true);
  };
  return (
    <div style={{ position: 'fixed', inset: 0, zIndex: 9999, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)' }}>
      <div style={{ width: '90%', maxWidth: 540, maxHeight: '80vh', background: bg0, border: `1px solid ${bdr}`, borderRadius: P.borderRadius.xl, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '1.25rem 1.5rem', borderBottom: `1px solid ${bdr}`, display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <LinkedInIcon />
          <span style={{ fontFamily: mono, fontSize: P.typography.fontSize.sm, letterSpacing: '0.08em', textTransform: 'uppercase', color: txt }}>Terms & Consent</span>
        </div>
        <div ref={scrollRef} onScroll={handleScroll} style={{ flex: 1, overflowY: 'auto', padding: '1.5rem', fontSize: P.typography.fontSize.sm, color: txt2, lineHeight: 1.8 }}>
          <h3 style={{ color: txt, marginBottom: '0.75rem', fontWeight: 500 }}>LinkedIn Data Access Consent</h3>
          <p>By clicking "I Agree", you consent to the following terms regarding your LinkedIn profile data:</p>
          <p style={{ marginTop: '1rem' }}><strong style={{ color: txt }}>1. Data Collection.</strong> We will access your public LinkedIn profile information including your name, headline, work experience, education, skills, certifications, and public posts. This data is collected solely to auto-fill your profile on the Founding Mindset platform and to provide AI-driven insights about your professional background.</p>
          <p style={{ marginTop: '0.75rem' }}><strong style={{ color: txt }}>2. Purpose.</strong> The collected data will be used exclusively for: (a) populating your profile fields, (b) analyzing your posts to discover areas of interest and expertise, (c) matching you with potential co-founders, and (d) generating personalized recommendations based on your professional background.</p>
          <p style={{ marginTop: '0.75rem' }}><strong style={{ color: txt }}>3. Data Processing.</strong> Your LinkedIn data may be processed by AI systems (OpenAI) to extract structured information such as skills, domains, and career insights. This processing is done in real-time and is not stored beyond what is saved to your profile on our platform.</p>
          <p style={{ marginTop: '0.75rem' }}><strong style={{ color: txt }}>4. Data Storage.</strong> Only the structured profile information extracted from your LinkedIn data will be stored in our database as part of your user profile. Raw LinkedIn API responses are not permanently stored.</p>
          <p style={{ marginTop: '0.75rem' }}><strong style={{ color: txt }}>5. Data Sharing.</strong> Your profile data may be visible to other users of the platform for co-founder matching purposes. We do not sell or share your data with third parties for marketing purposes.</p>
          <p style={{ marginTop: '0.75rem' }}><strong style={{ color: txt }}>6. Revocation.</strong> You can revoke this consent at any time by disconnecting your LinkedIn account from your profile settings. Previously collected data that has been saved to your profile will remain unless you manually delete it or request account deletion.</p>
          <p style={{ marginTop: '0.75rem' }}><strong style={{ color: txt }}>7. Security.</strong> We implement industry-standard security measures to protect your data including encrypted connections, secure token storage, and access controls.</p>
          <p style={{ marginTop: '1rem', fontSize: P.typography.fontSize.xs, color: txt2 }}>Last updated: April 2026. By proceeding, you acknowledge that you have read and understood these terms.</p>
        </div>
        <div style={{ padding: '1rem 1.5rem', borderTop: `1px solid ${bdr}`, display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', background: bg2 }}>
          <Button type="button" onClick={onCancel} variant="outline" size="sm">Cancel</Button>
          <Button type="button" onClick={onAgree} disabled={!scrolledToBottom} variant="primary" size="sm">
            {scrolledToBottom ? 'I Agree & Continue' : 'Scroll down to agree'}
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ─── Typeform-style Chatbot Overlay ─── */
function TypeformChat({ messages, chatInput, setChatInput, onSend, loading, extraCount, onClose }) {
  const chatEndRef = useRef(null);
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);
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
          <div style={{ fontSize: P.typography.fontSize.xs, letterSpacing: '0.12em', textTransform: 'uppercase', color: gold, fontFamily: mono }}>Founder Profiling</div>
          <div style={{ fontSize: P.typography.fontSize.sm, color: txt2, marginTop: 2 }}>
            {extraCount > 0 ? `${extraCount} insight${extraCount === 1 ? '' : 's'} collected` : 'Building your founder profile...'}
          </div>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: txt2, cursor: 'pointer', fontSize: 18, padding: 4 }} title="Minimize">&#x2715;</button>
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
          onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); onSend(); } }}
          placeholder="Type your answer..."
          style={{ ...inputStyle, flex: 1, minHeight: 46, borderRadius: '24px', paddingLeft: '1.1rem' }}
        />
        <button onClick={onSend} disabled={loading || !chatInput.trim()} style={{
          width: 46, height: 46, borderRadius: '50%', border: 'none',
          background: chatInput.trim() ? gold : bdr2, color: bg0,
          cursor: chatInput.trim() ? 'pointer' : 'default', fontSize: 18,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'background 0.2s',
        }}>&#x2191;</button>
      </div>
    </div>
  );
}

/* ─── Profile Completion Ring ─── */
function CompletionRing({ score }) {
  const r = 36, c = 2 * Math.PI * r, offset = c - (c * score / 100);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
      <svg width="84" height="84" viewBox="0 0 84 84">
        <circle cx="42" cy="42" r={r} fill="none" stroke={bdr2} strokeWidth="5" />
        <circle cx="42" cy="42" r={r} fill="none" stroke={gold} strokeWidth="5"
          strokeDasharray={c} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 42 42)"
          style={{ transition: 'stroke-dashoffset 0.8s ease-out' }} />
        <text x="42" y="46" textAnchor="middle" fill={txt} fontSize="16" fontFamily={mono} fontWeight="600">{score}%</text>
      </svg>
      <div>
        <div style={{ fontSize: P.typography.fontSize.xs, letterSpacing: '0.1em', textTransform: 'uppercase', color: txt2, fontFamily: mono }}>Profile Completion</div>
        <div style={{ fontSize: P.typography.fontSize.sm, color: score >= 80 ? '#0a6' : score >= 50 ? gold : errColor, marginTop: 2 }}>
          {score >= 80 ? 'Looking great!' : score >= 50 ? 'Getting there...' : 'Needs more info'}
        </div>
      </div>
    </div>
  );
}

/* ─── Dynamic Field Card (animated, auto-textarea for long values) ─── */
function DynamicFieldCard({ label: fieldLabel, value, onChange, isNew }) {
  const displayValue = Array.isArray(value) ? value.join(', ') : String(value || '');
  const isLong = displayValue.length > 50 || displayValue.includes(',');
  const filledStyle = { ...inputStyle, color: displayValue ? txt : txt2 };
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

  // LinkedIn OAuth
  const [linkedinAuthed, setLinkedinAuthed] = useState(Boolean(user.linkedinAuthed));
  const [linkedinAuthLoading, setLinkedinAuthLoading] = useState(false);
  const [showConsent, setShowConsent] = useState(false);
  const [authedLinkedinUrl, setAuthedLinkedinUrl] = useState(user.linkedinUrl || user.linkedin || '');
  const [authedName, setAuthedName] = useState('');
  const [authedEmail, setAuthedEmail] = useState('');

  // Typeform chatbot
  const [showChatbot, setShowChatbot] = useState(false);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Dynamic fields — split into scrape-discovered vs chatbot-collected
  const [extraFields, setExtraFields] = useState(user.extraFields || {});
  const [dynamicFieldLabels, setDynamicFieldLabels] = useState(user.dynamicFieldLabels || {});
  const [discoveredFields, setDiscoveredFields] = useState({});
  // Restore chatbot answers from DB on load using the stored key list
  const [chatbotAnswers, setChatbotAnswers] = useState(() => {
    const keys = user.chatbotFieldKeys || [];
    const extra = user.extraFields || {};
    const restored = {};
    keys.forEach(k => { if (extra[k] !== undefined) restored[k] = extra[k]; });
    return restored;
  });
  const [chatbotLabels, setChatbotLabels] = useState(() => {
    const keys = user.chatbotFieldKeys || [];
    const labels = user.dynamicFieldLabels || {};
    const restored = {};
    keys.forEach(k => { if (labels[k]) restored[k] = labels[k]; });
    return restored;
  });
  const [newFieldKeys, setNewFieldKeys] = useState(new Set());
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Profile completion — computed dynamically from all filled fields
  const profileCompletionScore = useMemo(() => {
    // Must-have fields (40% weight)
    const mustHave = ['firstName', 'lastName', 'headline', 'email', 'linkedinUrl'];
    const mustFilled = mustHave.filter(f => !blank(formData[f])).length;
    // Profile fields from scraping (30% weight)
    const profileFields = ['about', 'currentPosition', 'skills', 'tools', 'coreDomains', 'totalYearsExperience', 'workStyle'];
    const profileFilled = profileFields.filter(f => !blank(formData[f])).length;
    // Chatbot answers specifically (30% weight) — scrape insights don't count here
    // Only fields the user answered via chatbot count toward this
    const chatbotCount = Object.keys(chatbotAnswers).length;

    const mustScore = (mustFilled / mustHave.length) * 40;
    const profileScore = (profileFilled / profileFields.length) * 30;
    // 5+ chatbot answers = full 30% credit
    const chatbotScore = Math.min(chatbotCount, 5) / 5 * 30;
    return Math.min(100, Math.round(mustScore + profileScore + chatbotScore));
  }, [formData, chatbotAnswers]);

  // Track whether we already auto-filled from OAuth redirect
  const [oauthAutoFilled, setOauthAutoFilled] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('linkedin_success') === 'true') {
      setLinkedinAuthed(true);
      const urlFromCallback = params.get('linkedin_url');
      if (urlFromCallback) {
        setLinkedinUrlInput(urlFromCallback);
        setAuthedLinkedinUrl(urlFromCallback);
        setOauthAutoFilled(true);
      }
      const nameFromCallback = params.get('linkedin_name');
      if (nameFromCallback) {
        setAuthedName(nameFromCallback);
        // Auto-suggest URL from name if no URL came back from callback
        if (!urlFromCallback) {
          const suggested = `https://www.linkedin.com/in/${nameFromCallback.toLowerCase().replace(/\s+/g, '')}`;
          setLinkedinUrlInput(suggested);
        }
      }
      setSuccess(`LinkedIn authenticated${nameFromCallback ? ` as ${nameFromCallback}` : ''}! Confirm your URL and scrape.`);
      window.history.replaceState({}, '', window.location.pathname);
    } else if (params.get('linkedin_error')) {
      setError(`LinkedIn login failed: ${params.get('linkedin_error')}`);
      window.history.replaceState({}, '', window.location.pathname);
    }
    // Check persisted auth status, identity, and auto-fill URL
    linkedinAuthAPI.getStatus().then(res => {
      const data = res.data;
      setLinkedinAuthed(Boolean(data?.linkedinAuthed));
      if (data?.linkedinOAuthName) setAuthedName(data.linkedinOAuthName);
      if (data?.linkedinOAuthEmail) setAuthedEmail(data.linkedinOAuthEmail);
      if (data?.linkedinUrl) {
        // URL already stored from previous scrape — lock it
        setAuthedLinkedinUrl(data.linkedinUrl);
        setLinkedinUrlInput(data.linkedinUrl);
        setOauthAutoFilled(true);
      } else if (data?.linkedinAuthed && data?.linkedinOAuthName) {
        // No stored URL yet — auto-suggest from OAuth name so user doesn't have to type
        const suggested = `https://www.linkedin.com/in/${data.linkedinOAuthName.toLowerCase().replace(/\s+/g, '')}`;
        setLinkedinUrlInput(suggested);
      }
    }).catch(() => {});
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    setFormData(initialForm);
    const userLinkedinUrl = user.linkedinUrl || user.linkedin || '';
    // Don't overwrite URL if OAuth redirect already set it
    if (userLinkedinUrl && !oauthAutoFilled) setLinkedinUrlInput(userLinkedinUrl);
    setActiveScrapeUrl(normUrl(userLinkedinUrl));
    setAuthedLinkedinUrl(prev => prev || userLinkedinUrl);
    setExtraFields(user.extraFields || {});
    setDynamicFieldLabels(user.dynamicFieldLabels || {});
    setPostsScraped(0);
    setError(''); setSuccess('');
  }, [initialForm, user, oauthAutoFilled]);

  const tok = () => localStorage.getItem('token');
  const toArr = (v) => Array.isArray(v) ? v : splitList(v);

  // Disconnect LinkedIn — full wipe, fresh start
  const handleLinkedinDisconnect = async () => {
    if (!window.confirm('Disconnect LinkedIn? This will remove all LinkedIn data and require fresh authentication.')) return;
    try {
      await linkedinAuthAPI.disconnect();
      setLinkedinAuthed(false);
      setAuthedLinkedinUrl('');
      setAuthedName('');
      setAuthedEmail('');
      setLinkedinUrlInput('');
      setOauthAutoFilled(false);
      setSuccess('LinkedIn disconnected. All LinkedIn auth data removed.');
      onUpdate();
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to disconnect');
    }
  };

  // LinkedIn consent -> OAuth
  const handleLinkedinLoginClick = () => setShowConsent(true);
  const handleConsentAgree = async () => {
    setShowConsent(false);
    setLinkedinAuthLoading(true); setError('');
    try {
      const res = await linkedinAuthAPI.getConsentUrl();
      const url = res.data?.consentUrl || res.data?.details?.consentUrl;
      if (url) window.location.href = url;
      else setError('Failed to get LinkedIn consent URL');
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to initiate LinkedIn login');
    } finally { setLinkedinAuthLoading(false); }
  };

  // Scrape
  const handleScrape = async () => {
    if (!linkedinUrlInput.trim()) return setError('Please enter a LinkedIn URL');
    if (!linkedinAuthed) return setError('Please login with LinkedIn first');
    if (scrapeCooldown > 0) return setError(`Rate limit - wait ${scrapeCooldown}s`);
    setIsScraping(true); setError(''); setSuccess('');
    try {
      const requestedUrl = normUrl(linkedinUrlInput);
      if (requestedUrl && requestedUrl !== activeScrapeUrl) {
        setFormData(initialForm); setExtraFields({}); setDynamicFieldLabels({});
        setDiscoveredFields({}); setChatMessages([]); setPostsScraped(0);
      }
      const res = await axios.post(`${API}/api/profile/scrape-linkedin`, { linkedinUrl: linkedinUrlInput }, { headers: { Authorization: `Bearer ${tok()}` } });
      const d = res.data.details;
      const { profileData, postsScraped: ps, aiStatus, deepPostInsights, extraFields: sExtra, dynamicFieldLabels: sLabels } = d;
      setPostsScraped(ps || 0);
      const merged = mergeProfile(buildInitialForm({}), profileData);
      setFormData(merged);
      setActiveScrapeUrl(normUrl(profileData?.linkedinUrl || linkedinUrlInput));
      if (deepPostInsights) setDiscoveredFields(deepPostInsights);
      if (sExtra) { setExtraFields(prev => { const m = { ...prev, ...sExtra }; setNewFieldKeys(new Set(Object.keys(sExtra))); setTimeout(() => setNewFieldKeys(new Set()), 3000); return m; }); }
      if (sLabels) setDynamicFieldLabels(prev => ({ ...prev, ...sLabels }));
      setHasUnsavedChanges(true);
      setSuccess(`Profile auto-filled from LinkedIn.${ps > 0 ? ` ${ps} posts analyzed.` : ''}${aiStatus !== 'ok' ? ' (AI limited)' : ''} Click Save to persist.`);

      // Auto-popup typeform chatbot
      const intro = ps > 0
        ? `Great news! I analyzed your LinkedIn profile and ${ps} posts. I found some interesting insights about your expertise! Let me now understand your founder mindset better.`
        : `I've filled your profile from LinkedIn. Let me now learn about your founder/cofounder preferences to find you the best match.`;
      setChatMessages([{ role: 'model', text: intro }]);
      setShowChatbot(true);
      setChatLoading(true);
      try {
        const cr = await profileAPI.founderChat({ messages: [{ role: 'model', text: intro }], profileContext: merged, discoveredFields: deepPostInsights || {} });
        const cd = cr.data;
        const reply = cd?.reply || cd?.details?.reply;
        if (reply) setChatMessages(prev => [...prev, { role: 'model', text: reply }]);
      } catch { setChatMessages(prev => [...prev, { role: 'model', text: "Let's start! How many hours per week can you commit to a startup venture?" }]); }
      finally { setChatLoading(false); }
    } catch (e) {
      const status = e.response?.status;
      if (status === 403 && e.response?.data?.details?.requiresLinkedinAuth) { setLinkedinAuthed(false); setError('Please login with LinkedIn first.'); }
      else if (status === 429) { let s = 60; setScrapeCooldown(s); const t = setInterval(() => { s--; setScrapeCooldown(s); if (s <= 0) clearInterval(t); }, 1000); setError(`Rate limited - wait ${s}s`); }
      else setError(`Scraping failed: ${e.response?.data?.message || e.message}`);
    } finally { setIsScraping(false); }
  };

  // Founder chatbot
  const handleChatSend = useCallback(async () => {
    if (!chatInput.trim()) return;
    const updated = [...chatMessages, { role: 'user', text: chatInput }];
    setChatMessages(updated); setChatInput(''); setChatLoading(true);
    try {
      const res = await profileAPI.founderChat({ messages: updated, profileContext: formData, discoveredFields });
      const d = res.data || {};
      const newFields = d.extractedFields || {};
      const newLabels = d.fieldLabels || {};
      const allExtra = d.allExtraFields;
      const allLabels = d.allFieldLabels;

      // Use allExtraFields (full merged state from DB) if available,
      // otherwise merge newFields into local state
      if (Object.keys(newFields).length > 0) {
        setHasUnsavedChanges(true);
        setChatbotAnswers(prev => ({ ...prev, ...newFields }));
        setChatbotLabels(prev => ({ ...prev, ...newLabels }));
        setNewFieldKeys(new Set(Object.keys(newFields)));
        setTimeout(() => setNewFieldKeys(new Set()), 3000);
      }
      // Merge: server allExtra as base, then local extraFields, then new chatbot fields on top
      // Local state always wins over server state (nothing is saved until user clicks Save)
      setExtraFields(prev => ({ ...(allExtra || {}), ...prev, ...newFields }));
      setDynamicFieldLabels(prev => ({ ...(allLabels || {}), ...prev, ...newLabels }));

      const reply = d?.reply || d?.details?.reply;
      if (reply) setChatMessages(prev => [...prev, { role: 'model', text: reply }]);
      if (d?.conversationComplete || d?.details?.conversationComplete) {
        setChatMessages(prev => [...prev, { role: 'model', text: "I've built a comprehensive founder profile for you! Review the fields below and click Save Profile to persist everything." }]);
      }
    } catch (e) {
      setChatMessages(prev => [...prev, { role: 'model', text: e?.response?.status === 429 ? 'AI rate limited. Wait a moment.' : 'Something went wrong. Try again.' }]);
    } finally { setChatLoading(false); }
  }, [chatInput, chatMessages, formData, discoveredFields]);

  // Warn before leaving with unsaved changes
  useEffect(() => {
    const handler = (e) => { if (hasUnsavedChanges) { e.preventDefault(); e.returnValue = ''; } };
    window.addEventListener('beforeunload', handler);
    return () => window.removeEventListener('beforeunload', handler);
  }, [hasUnsavedChanges]);

  const handleChange = (e) => { const { name, value, type, checked } = e.target; setFormData(p => ({ ...p, [name]: type === 'checkbox' ? checked : value })); setHasUnsavedChanges(true); setError(''); };

  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError(''); setSuccess(''); setVectorStatus('');
    try {
      await profileAPI.updateProfile({
        ...formData, skills: toArr(formData.skills), tools: toArr(formData.tools), languages: toArr(formData.languages),
        coreDomains: toArr(formData.coreDomains), interests: toArr(formData.interests),
        experience_years: parseInt(formData.experience_years, 10) || parseInt(formData.totalYearsExperience, 10) || 0,
        extraFields: { ...extraFields, ...chatbotAnswers },
        dynamicFieldLabels: { ...dynamicFieldLabels, ...chatbotLabels },
        chatbotFieldKeys: Object.keys(chatbotAnswers),
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
  const extraFieldEntries = Object.entries(extraFields).filter(([, v]) => v !== null && v !== undefined && v !== '' && !(Array.isArray(v) && v.length === 0));

  return <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '1.5rem', fontFamily: mono, color: txt, background: bg0 }}>

    {/* Consent Modal */}
    {showConsent && <ConsentModal onAgree={handleConsentAgree} onCancel={() => setShowConsent(false)} />}

    {/* Typeform Chatbot */}
    {showChatbot && <TypeformChat messages={chatMessages} chatInput={chatInput} setChatInput={setChatInput} onSend={handleChatSend} loading={chatLoading} extraCount={extraFieldEntries.length} onClose={() => setShowChatbot(false)} />}

    {/* Header */}
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
      <h2 style={{ fontFamily: P.typography.fontFamily.display, fontSize: P.typography.fontSize['2xl'], fontWeight: 300, color: txt, letterSpacing: '0.04em', margin: 0 }}>Edit Profile</h2>
      <CompletionRing score={profileCompletionScore} />
    </div>

    {error && <div style={statusBanner(errColor, `${errColor}0d`, `1px solid ${errColor}44`)}>{error}</div>}
    {success && <div style={statusBanner(gold, `${gold}0d`, `1px solid ${gold}44`)}>{success}</div>}
    {vectorStatus === 'indexing' && <div style={statusBanner(txt2, `${bdr}22`, `1px solid ${bdr2}`)}>Updating talent index...</div>}
    {vectorStatus === 'done' && <div style={statusBanner(gold, `${gold}0d`, `1px solid ${gold}44`)}>Talent index updated.</div>}

    <form onSubmit={handleSubmit} autoComplete="off">

      {/* LinkedIn OAuth + Scrape */}
      <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden' }}>
        <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', flexWrap: 'wrap' }}>
            <LinkedInIcon /> LinkedIn Connect
            {linkedinAuthed && (
              <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, background: '#0a611a', color: '#0a6', border: '1px solid #0a644' }}>
                Connected{authedName ? ` — ${authedName}` : ''}{authedEmail && !authedName ? ` — ${authedEmail}` : ''}
              </span>
            )}
          </span>
          {linkedinAuthed && (
            <button type="button" onClick={handleLinkedinDisconnect} style={{ background: 'none', border: `1px solid ${errColor}44`, borderRadius: P.borderRadius.md, color: errColor, fontFamily: mono, fontSize: 10, padding: '3px 10px', cursor: 'pointer', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Disconnect
            </button>
          )}
        </div>
        <div style={{ padding: '1.25rem' }}>
          {!linkedinAuthed ? (
            <div style={{ textAlign: 'center', padding: '1.5rem' }}>
              <p style={{ fontSize: P.typography.fontSize.sm, color: txt2, marginBottom: '1rem', lineHeight: 1.6 }}>
                To scrape your LinkedIn profile, you first need to login with LinkedIn.<br />This ensures we have your consent to access your profile data.
              </p>
              <Button type="button" onClick={handleLinkedinLoginClick} disabled={linkedinAuthLoading} variant="primary" size="lg">
                <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <LinkedInIcon /> {linkedinAuthLoading ? 'Redirecting...' : 'Login with LinkedIn'}
                </span>
              </Button>
            </div>
          ) : (
            <>
              {/* Show connected identity */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1rem', padding: '0.75rem 1rem', background: '#00aa660d', border: '1px solid #0a644', borderRadius: P.borderRadius.md }}>
                <LinkedInIcon />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: P.typography.fontSize.sm, color: txt, fontWeight: 500 }}>{authedName || 'LinkedIn Account'}</div>
                  {authedEmail && <div style={{ fontSize: P.typography.fontSize.xs, color: txt2 }}>{authedEmail}</div>}
                </div>
                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, background: '#0a611a', color: '#0a6', border: '1px solid #0a644' }}>Verified</span>
              </div>

              {authedLinkedinUrl ? (
                <>
                  {/* URL is locked — already scraped before */}
                  <p style={{ fontSize: P.typography.fontSize.xs, color: txt2, marginBottom: '0.6rem' }}>Your LinkedIn profile is locked to your authenticated account.</p>
                  <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <div style={{ ...inputStyle, flex: 1, minWidth: 220, background: bg2, color: txt2, cursor: 'not-allowed', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                      {authedLinkedinUrl}
                    </div>
                    <Button type="button" onClick={handleScrape} disabled={isScraping || scrapeCooldown > 0} variant="primary" size="sm">
                      {isScraping ? 'Scraping...' : scrapeCooldown > 0 ? `Wait ${scrapeCooldown}s` : 'Scrape & Auto-fill'}
                    </Button>
                  </div>
                </>
              ) : (
                <>
                  <p style={{ fontSize: P.typography.fontSize.xs, color: txt2, marginBottom: '0.6rem' }}>
                    Your LinkedIn profile URL is locked to your authenticated account.
                  </p>
                  <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}>
                    <div style={{ ...inputStyle, flex: 1, minWidth: 220, background: bg2, color: txt2, cursor: 'not-allowed', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
                      {linkedinUrlInput || `https://www.linkedin.com/in/${(authedName || '').toLowerCase().replace(/\s+/g, '')}`}
                    </div>
                    <Button type="button" onClick={handleScrape} disabled={isScraping || scrapeCooldown > 0 || !linkedinUrlInput.trim()} variant="primary" size="sm">
                      {isScraping ? 'Scraping...' : 'Scrape & Auto-fill'}
                    </Button>
                  </div>
                </>
              )}
              {postsScraped > 0 && <p style={{ fontSize: 11, color: txt2, marginTop: '0.75rem' }}>{postsScraped} posts deeply analyzed.</p>}
            </>
          )}
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

      {/* Discovered from LinkedIn (scrape insights - not chatbot) */}
      {(() => {
        const chatKeys = new Set(Object.keys(chatbotAnswers));
        const scrapeEntries = extraFieldEntries.filter(([k]) => !chatKeys.has(k));
        return scrapeEntries.length > 0 && (
          <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
            <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                Discovered from LinkedIn
                <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${bdr2}`, color: txt2 }}>{scrapeEntries.length} insights</span>
              </span>
            </div>
            <div style={{ padding: '1.25rem' }}>
              <div style={grid(2)}>
                {scrapeEntries.map(([key, value]) => {
                  const fl = dynamicFieldLabels[key] || key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase()).trim();
                  return (
                    <DynamicFieldCard key={key} label={fl} value={value} isNew={newFieldKeys.has(key)}
                      onChange={(e) => { setExtraFields(prev => ({ ...prev, [key]: e.target.value })); setHasUnsavedChanges(true); }} />
                  );
                })}
              </div>
            </div>
          </div>
        );
      })()}

      {/* Additional Questions — Chatbot-collected founder profile fields */}
      {(() => {
        const chatEntries = Object.entries(chatbotAnswers).filter(([, v]) => v !== null && v !== undefined && v !== '' && !(Array.isArray(v) && v.length === 0));
        return (
          <div style={{ marginBottom: '1.5rem', border: `1px solid ${gold}33`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
            <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: `${gold}0a`, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: gold, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
              <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                Founder Profile — Additional Questions
                {chatEntries.length > 0 && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${gold}66`, background: `${gold}18` }}>{chatEntries.length} answers</span>}
              </span>
              {!showChatbot && (
                <button type="button" onClick={() => {
                  if (!chatMessages.length) setChatMessages([{ role: 'model', text: "Hi! I'm your founder profiling assistant. Tell me about your startup ambitions and I'll build your co-founder matching profile." }]);
                  setShowChatbot(true);
                }} style={{
                  background: `${gold}18`, border: `1px solid ${gold}44`, borderRadius: P.borderRadius.full,
                  color: gold, fontFamily: mono, fontSize: P.typography.fontSize.xs, padding: '0.4rem 0.9rem',
                  cursor: 'pointer', letterSpacing: '0.06em',
                }}>{chatEntries.length > 0 ? '+ Continue Chat' : '+ Start Chat'}</button>
              )}
            </div>
            <div style={{ padding: '1.25rem' }}>
              {chatEntries.length > 0 ? (
                <div style={grid(2)}>
                  {chatEntries.map(([key, value]) => {
                    const fl = chatbotLabels[key] || dynamicFieldLabels[key] || key.replace(/_/g, ' ').replace(/([A-Z])/g, ' $1').replace(/^./, s => s.toUpperCase()).trim();
                    return (
                      <DynamicFieldCard key={key} label={fl} value={value} isNew={newFieldKeys.has(key)}
                        onChange={(e) => { setChatbotAnswers(prev => ({ ...prev, [key]: e.target.value })); setExtraFields(prev => ({ ...prev, [key]: e.target.value })); setHasUnsavedChanges(true); }} />
                    );
                  })}
                </div>
              ) : (
                <p style={{ fontSize: P.typography.fontSize.sm, color: txt2, textAlign: 'center', padding: '1rem 0', lineHeight: 1.6 }}>
                  No answers collected yet. Open the Founder Chat to answer questions about your availability, equity preferences, leadership style, and more. Each answer creates a field here.
                </p>
              )}
            </div>
          </div>
        );
      })()}

      {hasUnsavedChanges && <div style={statusBanner(gold, `${gold}0d`, `1px solid ${gold}44`)}>You have unsaved changes. Click Save to persist your profile to the database and enable matching.</div>}
      <Button type="submit" disabled={loading} variant="primary" size="lg" fullWidth>{loading ? 'Saving...' : hasUnsavedChanges ? 'Save Profile (unsaved changes)' : 'Save Profile'}</Button>
    </form>

    {/* Floating chat trigger */}
    {!showChatbot && linkedinAuthed && (
      <button onClick={() => { if (!chatMessages.length) setChatMessages([{ role: 'model', text: "Hi! I'm your founder profiling assistant. Tell me about your startup ambitions and I'll build your co-founder matching profile." }]); setShowChatbot(true); }}
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
