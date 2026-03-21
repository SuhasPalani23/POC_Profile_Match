import React, { useEffect, useMemo, useState } from 'react';
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
const err = P.colors.status.error;
const mono = P.typography.fontFamily.primary;
const listFields = new Set(['skills', 'tools', 'languages', 'coreDomains', 'interests']);
const chatbotFields = ['firstName','lastName','headline','about','currentPosition','currentCompany','totalYearsExperience','skills','tools','coreDomains','interests','careerGoals','github','email','phone','preferredRole','preferredIndustry','languages','skillStrength','workStyle','hobbies','strengths','industryInclination'];
const input = { width: '100%', padding: '0.7rem 0.9rem', background: bg1, border: `1px solid ${bdr2}`, borderRadius: P.borderRadius.md, color: txt, fontSize: P.typography.fontSize.sm, fontFamily: mono, boxSizing: 'border-box', outline: 'none' };
const label = { display: 'block', fontSize: P.typography.fontSize.xs, letterSpacing: '0.12em', textTransform: 'uppercase', color: txt2, marginBottom: '0.45rem', fontFamily: mono };

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
const statusStyle = (color, bg, border) => ({ padding: '0.75rem 1rem', marginBottom: '1rem', border, borderRadius: P.borderRadius.md, color, background: bg, fontSize: P.typography.fontSize.sm });
const grid = (cols = 2) => ({ display: 'grid', gridTemplateColumns: `repeat(auto-fit, minmax(${cols === 3 ? 160 : 220}px, 1fr))`, gap: '0 1rem' });

const Section = ({ title, badge, defaultOpen = true, children }) => {
  const [open, setOpen] = useState(defaultOpen);
  return <div style={{ marginBottom: '1.5rem', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden' }}><button type="button" onClick={() => setOpen((v) => !v)} style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, border: 'none', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}><span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>{title}{badge > 0 && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${gold}66`, color: gold, background: `${gold}18` }}>{badge} missing</span>}</span><span style={{ color: txt2 }}>{open ? '▲' : '▼'}</span></button>{open && <div style={{ padding: '1.25rem' }}>{children}</div>}</div>;
};
const Field = ({ text, children }) => <div style={{ marginBottom: '1.15rem' }}><label style={label}>{text}</label>{children}</div>;
const ChatbotIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    <path d="M21 12a8.5 8.5 0 0 1-8.5 8.5H7l-4 3v-6.5A8.5 8.5 0 1 1 21 12Z" />
    <path d="M8 10h8" />
    <path d="M8 14h5" />
  </svg>
);

export default function ProfileEdit({ user, onUpdate }) {
  const initialForm = useMemo(() => buildInitialForm(user), [user]);
  const initialChatMessage = "Hello. I'll help complete your profile one missing field at a time.";
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
  const [showChatbot, setShowChatbot] = useState(false);
  const [missingFields, setMissingFields] = useState([]);
  const [chatMessages, setChatMessages] = useState([{ role: 'model', text: initialChatMessage }]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [scrapeCooldown, setScrapeCooldown] = useState(0);

  useEffect(() => {
    setFormData(initialForm);
    setLinkedinUrlInput(user.linkedinUrl || user.linkedin || '');
    setActiveScrapeUrl(normUrl(user.linkedinUrl || user.linkedin || ''));
    setShowChatbot(false);
    setMissingFields([]);
    setChatMessages([{ role: 'model', text: initialChatMessage }]);
    setChatInput('');
    setPostsScraped(0);
    setError('');
    setSuccess('');
  }, [initialForm, user]);

  const tok = () => localStorage.getItem('token');
  const toArr = (v) => Array.isArray(v) ? v : splitList(v);
  const computeMissing = (data) => chatbotFields.filter((f) => blank(data[f]));
  const assistantMessages = (details = {}) => {
    const reply = String(details.reply || '').trim();
    const q = String(details.nextQuestion || '').trim();
    const out = [];
    if (reply) out.push({ role: 'model', text: reply });
    if (q && (!reply || !reply.toLowerCase().includes(q.toLowerCase()))) out.push({ role: 'model', text: q });
    return out;
  };
  const askNext = async (messages, currentForm, currentMissing) => {
    const res = await axios.post(`${API}/api/profile/chat-fill`, { messages, missingFields: currentMissing, profileContext: currentForm }, { headers: { Authorization: `Bearer ${tok()}` } });
    return res.data.details;
  };
  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((p) => ({ ...p, [name]: type === 'checkbox' ? checked : value }));
    setError('');
  };
  const handleScrape = async () => {
    if (!linkedinUrlInput.trim()) return setError('Please enter a LinkedIn URL');
    if (scrapeCooldown > 0) return setError(`Rate limit active - please wait ${scrapeCooldown}s before trying again.`);
    setIsScraping(true); setError(''); setSuccess('');
    try {
      const requestedUrl = normUrl(linkedinUrlInput);
      const isNewLinkedinTarget = Boolean(requestedUrl && requestedUrl !== activeScrapeUrl);
      if (isNewLinkedinTarget) {
        setFormData(initialForm);
        setMissingFields([]);
        setChatMessages([
          { role: 'model', text: 'Starting a new LinkedIn scrape session.' },
          { role: 'model', text: 'I cleared the previous unsaved assistant flow for this new profile URL.' },
        ]);
        setChatInput('');
        setPostsScraped(0);
        setShowChatbot(true);
      }
      const res = await axios.post(`${API}/api/profile/scrape-linkedin`, { linkedinUrl: linkedinUrlInput }, { headers: { Authorization: `Bearer ${tok()}` } });
      const { profileData, missingFields: serverMissing, postsScraped: ps, aiStatus } = res.data.details;
      setPostsScraped(ps || 0);
      const incoming = normUrl(profileData?.linkedinUrl || linkedinUrlInput);
      const merged = mergeProfile(buildInitialForm({}), profileData);
      setFormData(merged);
      setActiveScrapeUrl(incoming);
      const allMissing = Array.from(new Set([...computeMissing(merged), ...(serverMissing || [])]));
      setMissingFields(allMissing);
      if (!allMissing.length) {
        const suffix = ps > 0 ? ` (${ps} posts analysed)` : '';
        const aiNote = aiStatus && aiStatus !== 'ok' ? ' (AI enrichment unavailable - basic profile filled)' : '';
        setSuccess(`Profile auto-filled successfully.${suffix}${aiNote}`);
        setChatMessages([
          { role: 'model', text: 'I auto-filled your profile from LinkedIn.' },
          { role: 'model', text: 'Profile looks complete. I will stay here if you want to add or change anything else in your profile.' },
        ]);
        setShowChatbot(true);
        return;
      }
      const intro = [{ role: 'model', text: "I've auto-filled your profile from LinkedIn. I still need a few details to complete it, and I'll ask them one at a time." }];
      setChatMessages(intro); setShowChatbot(true); setChatLoading(true);
      try {
        const details = await askNext(intro, merged, allMissing);
        setMissingFields(details.remainingFields || allMissing);
        const msgs = assistantMessages(details);
        if (msgs.length) setChatMessages([...intro, ...msgs]);
      } catch {
        setChatMessages([...intro, { role: 'model', text: 'I still need a few more details. What is your GitHub profile URL?' }]);
      } finally { setChatLoading(false); }
    } catch (e) {
      const status = e.response?.status;
      const msg = e.response?.data?.message || e.response?.data?.error || e.message;
      if (status === 429) {
        let secs = Number(e.response?.data?.details?.retry_after_seconds) || 60;
        setScrapeCooldown(secs);
        const timer = setInterval(() => { secs -= 1; setScrapeCooldown(secs); if (secs <= 0) clearInterval(timer); }, 1000);
        setError(e.response?.data?.message || `Rate limit hit - button will re-enable in ${secs} seconds. Please wait.`);
      } else setError(`Scraping failed: ${msg}`);
    } finally { setIsScraping(false); }
  };
  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const next = [...chatMessages, { role: 'user', text: chatInput }];
    setChatMessages(next); setChatInput('');
    try {
      setChatLoading(true);
      const details = await askNext(next, formData, missingFields);
      const merged = mergeProfile(formData, details.updatedData || {});
      setFormData(merged);
      const remaining = details.remainingFields || computeMissing(merged);
      setMissingFields(remaining);
      const msgs = assistantMessages(details);
      setChatMessages((p) => [...p, ...(msgs.length ? msgs : [{ role: 'model', text: 'Thanks. I updated that detail in the form.' }])]);
      if (!remaining.length) {
        setSuccess('Profile complete! Review below and save.');
        setChatMessages((p) => (
          p[p.length - 1]?.text === 'Everything important is filled now. I will stay here if you want to add or change anything else in your profile.'
            ? p
            : [...p, { role: 'model', text: 'Everything important is filled now. I will stay here if you want to add or change anything else in your profile.' }]
        ));
      }
    } catch (e) {
      const status = e?.response?.status;
      setChatMessages((p) => [...p, { role: 'model', text: status === 429 ? 'The AI assistant is rate-limited right now. Your edits are still here, and you can continue after a short wait.' : 'Something went wrong. Please try again.' }]);
    } finally { setChatLoading(false); }
  };
  const handleSubmit = async (e) => {
    e.preventDefault(); setLoading(true); setError(''); setSuccess(''); setVectorStatus('');
    try {
      await profileAPI.updateProfile({ ...formData, skills: toArr(formData.skills), tools: toArr(formData.tools), languages: toArr(formData.languages), coreDomains: toArr(formData.coreDomains), interests: toArr(formData.interests), experience_years: parseInt(formData.experience_years, 10) || parseInt(formData.totalYearsExperience, 10) || 0 });
      setSuccess('Profile saved.'); setVectorStatus('indexing'); setTimeout(() => { setVectorStatus('done'); onUpdate(); }, 3500);
    } catch (e2) { setError(e2.response?.data?.error || 'Failed to save profile'); } finally { setLoading(false); }
  };
  const handleResumeChange = (e) => {
    const f = e.target.files?.[0]; if (!f) return;
    if (!['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'].includes(f.type)) return setError('Only PDF and DOCX allowed');
    if (f.size > 10 * 1024 * 1024) return setError('Max 10MB');
    setResume(f); setError('');
  };
  const handleResumeUpload = async () => {
    if (!resume) return setError('Select a file first');
    setUploadingResume(true); setError(''); setVectorStatus('');
    try {
      const fd = new FormData(); fd.append('resume', resume); const res = await profileAPI.uploadResume(fd);
      setSuccess('Resume uploaded and analysed.'); setVectorStatus('indexing'); setResumeAnalysis(res.data.details?.analysis || null); setResume(null);
      if (res.data.details?.analysis?.merged_skills) setFormData((p) => ({ ...p, skills: res.data.details.analysis.merged_skills.join(', ') }));
      setTimeout(() => { setVectorStatus('done'); onUpdate(); }, 3500);
    } catch (e) { setError(e.response?.data?.error || 'Upload failed'); } finally { setUploadingResume(false); }
  };
  const handleDownloadResume = async () => {
    setDownloadingResume(true); setError('');
    try {
      const res = await profileAPI.getResume(user._id); const blob = new Blob([res.data], { type: res.headers['content-type'] || 'application/pdf' }); const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = user.resume || 'resume.pdf'; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
    } catch (e) {
      const d = e.response?.data;
      if (d instanceof Blob) { try { const t = JSON.parse(await d.text()); setError(t.error || 'Download failed'); } catch { setError('Download failed'); } }
      else setError(e.response?.data?.error || 'Download failed');
    } finally { setDownloadingResume(false); }
  };
  const handleDeleteResume = async () => {
    if (!window.confirm('Delete your resume?')) return;
    try { await profileAPI.deleteResume(); setSuccess('Resume deleted.'); setVectorStatus('indexing'); setTimeout(() => { setVectorStatus('done'); onUpdate(); }, 3500); } catch (e) { setError(e.response?.data?.error || 'Delete failed'); }
  };

  const missing1 = ['firstName','lastName','headline','city','state','country','currentPosition','currentCompany','totalYearsExperience','about'].filter((f) => blank(formData[f])).length;
  const missing2 = ['skills','tools','coreDomains','interests','industryInclination','skillStrength','careerGoals','preferredRole','preferredIndustry','strengths','workStyle','hobbies','github','email','phone','languages'].filter((f) => blank(formData[f])).length;

  return <div style={{ maxWidth: '1240px', margin: '0 auto', padding: '1.5rem', fontFamily: mono, color: txt, background: bg0 }}>
    <div style={{ display: 'grid', gridTemplateColumns: showChatbot ? 'minmax(0, 1fr) 360px' : 'minmax(0, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
      <div style={{ minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
          <h2 style={{ fontFamily: P.typography.fontFamily.display, fontSize: P.typography.fontSize['2xl'], fontWeight: 300, color: txt, letterSpacing: '0.04em', margin: 0 }}>Edit Profile</h2>
          <button
            type="button"
            onClick={() => setShowChatbot((prev) => !prev)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.55rem',
              padding: '0.75rem 1rem',
              borderRadius: P.borderRadius.full,
              border: `1px solid ${showChatbot ? `${gold}88` : bdr2}`,
              background: showChatbot ? `${gold}14` : bg1,
              color: showChatbot ? gold : txt,
              fontFamily: mono,
              fontSize: P.typography.fontSize.xs,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              cursor: 'pointer',
            }}
          >
            <ChatbotIcon />
            {showChatbot ? 'Hide Assistant' : 'Open Assistant'}
          </button>
        </div>
        {error && <div style={statusStyle(err, `${err}0d`, `1px solid ${err}44`)}>{error}</div>}
        {success && <div style={statusStyle(gold, `${gold}0d`, `1px solid ${gold}44`)}>{success}</div>}
        {vectorStatus === 'indexing' && <div style={statusStyle(txt2, `${bdr}22`, `1px solid ${bdr2}`)}>Updating talent index...</div>}
        {vectorStatus === 'done' && <div style={statusStyle(gold, `${gold}0d`, `1px solid ${gold}44`)}>Talent index updated.</div>}
        <form onSubmit={handleSubmit} autoComplete="off">
      <Section title="LinkedIn Auto-Fill" defaultOpen={true}><p style={{ fontSize: P.typography.fontSize.xs, color: txt2, marginBottom: '0.9rem', letterSpacing: '0.04em' }}>Paste your LinkedIn URL to auto-fill profile data and recent posts.</p><div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap' }}><input type="url" placeholder="https://www.linkedin.com/in/username" value={linkedinUrlInput} onChange={(e) => setLinkedinUrlInput(e.target.value)} style={{ ...input, flex: 1, minWidth: 220 }} /><Button type="button" onClick={handleScrape} disabled={isScraping || scrapeCooldown > 0} variant="primary" size="sm">{isScraping ? 'Scraping...' : scrapeCooldown > 0 ? `Wait ${scrapeCooldown}s...` : 'Scrape & Auto-fill'}</Button></div>{postsScraped > 0 && <p style={{ fontSize: 11, color: txt2, marginTop: '0.5rem' }}>{postsScraped} posts analysed for domains and interests.</p>}</Section>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '1.5rem', alignItems: 'start' }}>
        <div style={{ border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
          <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>General Info{missing1 > 0 && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${gold}66`, color: gold, background: `${gold}18` }}>{missing1} missing</span>}</span>
          </div>
          <div style={{ padding: '1.25rem' }}>
            <div style={grid(2)}><Field text="First Name"><input name="firstName" value={formData.firstName} onChange={handleChange} style={input} placeholder="John" /></Field><Field text="Last Name"><input name="lastName" value={formData.lastName} onChange={handleChange} style={input} placeholder="Doe" /></Field></div>
            <Field text="Professional Headline"><input name="headline" value={formData.headline} onChange={handleChange} style={input} placeholder="Senior ML Engineer | Building intelligent systems" /></Field>
            <div style={grid(3)}><Field text="City"><input name="city" value={formData.city} onChange={handleChange} style={input} placeholder="Mumbai" /></Field><Field text="State"><input name="state" value={formData.state} onChange={handleChange} style={input} placeholder="MH" /></Field><Field text="Country"><input name="country" value={formData.country} onChange={handleChange} style={input} placeholder="India" /></Field></div>
            <div style={grid(2)}><Field text="Current Role"><input name="currentPosition" value={formData.currentPosition} onChange={handleChange} style={input} placeholder="Software Engineer" /></Field><Field text="Current Company"><input name="currentCompany" value={formData.currentCompany} onChange={handleChange} style={input} placeholder="Google" /></Field></div>
            <Field text="Years of Experience"><input name="totalYearsExperience" value={formData.totalYearsExperience} onChange={handleChange} style={input} type="number" min="0" placeholder="3" /></Field>
            <Field text="Bio / About Me"><textarea name="about" value={formData.about} onChange={handleChange} style={{ ...input, minHeight: 100, resize: 'vertical' }} placeholder="Write your professional summary..." /></Field>
          </div>
        </div>
        <div style={{ border: `1px solid ${bdr}`, borderRadius: P.borderRadius.lg, overflow: 'hidden', background: bg0 }}>
          <div style={{ width: '100%', padding: '0.95rem 1.25rem', background: bg2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', color: txt, fontFamily: mono, fontSize: P.typography.fontSize.xs, letterSpacing: '0.14em', textTransform: 'uppercase' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>Additional Info{missing2 > 0 && <span style={{ fontSize: 10, padding: '2px 8px', borderRadius: 999, border: `1px solid ${gold}66`, color: gold, background: `${gold}18` }}>{missing2} missing</span>}</span>
          </div>
          <div style={{ padding: '1.25rem' }}>
            <div style={{ marginBottom: '1.5rem', padding: '1rem', border: `1px solid ${bdr2}`, borderRadius: P.borderRadius.md }}><p style={{ ...label, marginBottom: '0.8rem' }}>Resume (PDF / DOCX)</p><input type="file" accept=".pdf,.docx,.doc" onChange={handleResumeChange} style={{ fontSize: P.typography.fontSize.xs, color: txt2, marginBottom: '0.8rem', display: 'block' }} /><div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}><Button type="button" onClick={handleResumeUpload} disabled={uploadingResume || !resume} variant="primary" size="sm">{uploadingResume ? 'Uploading...' : 'Upload'}</Button>{user.resume && <><Button type="button" onClick={handleDownloadResume} disabled={downloadingResume} variant="secondary" size="sm">{downloadingResume ? 'Downloading...' : 'Download'}</Button><Button type="button" onClick={handleDeleteResume} variant="outline" size="sm">Delete</Button></>}</div>{resumeAnalysis?.merged_skills?.length > 0 && <p style={{ fontSize: 11, color: txt2, marginTop: '0.6rem' }}>Extracted skills: {resumeAnalysis.merged_skills.join(', ')}</p>}</div>
            <Field text="Skills (comma-separated)"><textarea name="skills" value={formData.skills} onChange={handleChange} style={{ ...input, minHeight: 70, resize: 'vertical' }} placeholder="Python, React, SQL, Figma..." /></Field>
            <Field text="Tools & Technologies"><textarea name="tools" value={formData.tools} onChange={handleChange} style={{ ...input, minHeight: 70, resize: 'vertical' }} placeholder="VS Code, Docker, AWS, Notion..." /></Field>
            <div style={grid(2)}><Field text="Core Domains"><input name="coreDomains" value={formData.coreDomains} onChange={handleChange} style={input} placeholder="Machine Learning, Web Dev..." /></Field><Field text="Interests (from posts)"><input name="interests" value={formData.interests} onChange={handleChange} style={input} placeholder="AI, Open Source, Startups..." /></Field></div>
            <div style={grid(2)}><Field text="Industry Inclination"><input name="industryInclination" value={formData.industryInclination} onChange={handleChange} style={input} placeholder="FinTech, HealthTech..." /></Field><Field text="Skill Strength"><select name="skillStrength" value={formData.skillStrength} onChange={handleChange} style={input}><option value="">Select...</option>{['Beginner','Intermediate','Advanced','Expert'].map((o) => <option key={o} value={o}>{o}</option>)}</select></Field></div>
            <Field text="Career Goals"><textarea name="careerGoals" value={formData.careerGoals} onChange={handleChange} style={{ ...input, minHeight: 70, resize: 'vertical' }} placeholder="I want to lead AI research teams..." /></Field>
            <div style={grid(2)}><Field text="Preferred Role"><input name="preferredRole" value={formData.preferredRole} onChange={handleChange} style={input} placeholder="AI Engineer, PM..." /></Field><Field text="Preferred Industry"><input name="preferredIndustry" value={formData.preferredIndustry} onChange={handleChange} style={input} placeholder="SaaS, FinTech..." /></Field></div>
            <Field text="Strengths"><textarea name="strengths" value={formData.strengths} onChange={handleChange} style={{ ...input, minHeight: 70, resize: 'vertical' }} placeholder="Critical thinking, fast learner..." /></Field>
            <div style={grid(2)}><Field text="Work Style"><select name="workStyle" value={formData.workStyle} onChange={handleChange} style={input}><option value="">Select...</option>{['Team','Individual','Remote','Hybrid'].map((o) => <option key={o} value={o}>{o}</option>)}</select></Field><Field text="Open to Work"><div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.65rem' }}><input type="checkbox" name="openToWork" checked={formData.openToWork} onChange={handleChange} style={{ width: 16, height: 16, accentColor: gold }} /><span style={{ fontSize: P.typography.fontSize.sm, color: txt2 }}>Actively looking</span></div></Field></div>
            <Field text="Hobbies"><input name="hobbies" value={formData.hobbies} onChange={handleChange} style={input} placeholder="Photography, hiking, gaming..." /></Field>
            <Field text="Languages"><input name="languages" value={formData.languages} onChange={handleChange} style={input} placeholder="English, Hindi..." /></Field>
            <div style={grid(2)}><Field text="LinkedIn URL"><input name="linkedinUrl" value={formData.linkedinUrl} onChange={handleChange} style={input} placeholder="https://linkedin.com/in/..." /></Field><Field text="GitHub URL"><input name="github" value={formData.github} onChange={handleChange} style={input} placeholder="https://github.com/..." /></Field></div>
            <div style={grid(2)}><Field text="Email"><input name="email" value={formData.email} onChange={handleChange} style={input} type="email" placeholder="you@example.com" /></Field><Field text="Phone"><input name="phone" value={formData.phone} onChange={handleChange} style={input} placeholder="+91 98765 43210" /></Field></div>
          </div>
        </div>
      </div>
          <Button type="submit" disabled={loading} variant="primary" size="lg" fullWidth>{loading ? 'Saving...' : 'Save Profile'}</Button>
        </form>
      </div>
      {showChatbot && (
        <aside style={{ position: 'sticky', top: '96px', height: 'calc(100vh - 112px)', minHeight: '560px', border: `1px solid ${bdr}`, borderRadius: P.borderRadius.xl, background: bg0, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
          <div style={{ padding: '1rem 1.1rem', background: `linear-gradient(180deg, ${gold}12, transparent)`, borderBottom: `1px solid ${bdr}` }}>
            <div style={{ fontSize: P.typography.fontSize.xs, letterSpacing: '0.12em', textTransform: 'uppercase', color: gold, marginBottom: '0.35rem' }}>AI Profile Assistant</div>
            <div style={{ fontSize: P.typography.fontSize.sm, color: txt2, lineHeight: 1.5 }}>
              {missingFields.length > 0
                ? `${missingFields.length} field${missingFields.length === 1 ? '' : 's'} still need your input.`
                : 'Profile looks complete. This assistant stays here if you still want to change anything.'}
            </div>
          </div>
          <div style={{ padding: '1rem', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.75rem', background: 'linear-gradient(180deg, rgba(255,255,255,0.01), transparent 28%)' }}>
            {chatMessages.map((m, i) => (
              <div key={`${m.role}-${i}`} style={{ alignSelf: m.role === 'user' ? 'flex-end' : 'flex-start', width: 'fit-content', maxWidth: '88%', padding: '0.8rem 0.95rem', borderRadius: m.role === 'user' ? '18px 18px 6px 18px' : '18px 18px 18px 6px', background: m.role === 'user' ? `${gold}1f` : '#111214', border: `1px solid ${m.role === 'user' ? `${gold}55` : bdr}`, fontSize: P.typography.fontSize.sm, color: txt, lineHeight: 1.65, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{m.text}</div>
            ))}
          </div>
          <div style={{ padding: '0.75rem 1rem 1rem', borderTop: `1px solid ${bdr}`, display: 'flex', gap: '0.5rem', alignItems: 'flex-end', background: bg0 }}>
            <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') { e.preventDefault(); handleChatSend(); } }} placeholder="Type your answer..." style={{ ...input, flex: 1, minHeight: 46 }} />
            <Button type="button" onClick={handleChatSend} disabled={chatLoading} variant="primary" size="sm">Send</Button>
          </div>
        </aside>
      )}
    </div>
  </div>;
}
