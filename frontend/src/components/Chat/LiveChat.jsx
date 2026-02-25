import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { chatAPI, collaborationAPI } from '../../services/api';
import { useWebSocket } from '../../utils/websocket';
import Button from '../Common/Button';
import palette from '../../palette';

const LiveChat = ({ user }) => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { socket, joinProject, leaveProject } = useWebSocket();

  // Chat mode: 'group' | dm_<userId>
  const [chatMode, setChatMode] = useState('group');
  const [groupMessages, setGroupMessages] = useState([]);
  const [dmMessages, setDmMessages] = useState({}); // keyed by other user id
  const [newMessage, setNewMessage] = useState('');
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(null); // { collaboration_id, name }
  const messagesEndRef = useRef(null);

  const isFounder = team && team.founder.user_id === user._id;
  const activeDmUserId = chatMode.startsWith('dm_') ? chatMode.replace('dm_', '') : null;
  const currentMessages = activeDmUserId
    ? (dmMessages[activeDmUserId] || [])
    : groupMessages;

  useEffect(() => {
    loadChatData();
    if (socket) {
      joinProject(projectId);
      socket.on('new_message', handleNewMessage);
      socket.on('new_dm', handleNewDm);
      socket.on('member_left', () => loadChatData());
    }
    return () => {
      if (socket) {
        leaveProject(projectId);
        socket.off('new_message', handleNewMessage);
        socket.off('new_dm', handleNewDm);
        socket.off('member_left');
      }
    };
  }, [projectId, socket]);

  // Join DM room when switching to DM mode
  useEffect(() => {
    if (!socket || !activeDmUserId) return;
    socket.emit('join_dm', { other_user_id: activeDmUserId, token: localStorage.getItem('token') });
    // Load DM history if not loaded
    if (!dmMessages[activeDmUserId]) {
      chatAPI.getDMMessages(projectId, activeDmUserId)
        .then(r => setDmMessages(prev => ({ ...prev, [activeDmUserId]: r.data.messages })))
        .catch(() => {});
    }
    return () => {
      if (socket) socket.emit('leave_dm', { other_user_id: activeDmUserId, token: localStorage.getItem('token') });
    };
  }, [activeDmUserId, socket]);

  useEffect(() => { scrollToBottom(); }, [currentMessages]);

  const loadChatData = async () => {
    try {
      const teamRes = await collaborationAPI.getTeamMembers(projectId);
      setTeam(teamRes.data);
      const msgRes = await chatAPI.getMessages(projectId);
      setGroupMessages(msgRes.data.messages);
    } catch {
      alert('Failed to load chat. You may not have access to this project.');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  // Dedup helper — prevents double-add when sender also receives their own WS event
  const addMessageDeduped = (setter, msg) => {
    setter(prev => {
      const id = msg.message_id || msg._id;
      if (id && prev.some(m => (m.message_id || m._id) === id)) return prev;
      return [...prev, msg];
    });
  };

  const handleNewMessage = (msg) => {
    if (msg.dm_recipient_id) {
      const otherId = msg.sender_id === user._id ? msg.dm_recipient_id : msg.sender_id;
      setDmMessages(prev => {
        const thread = prev[otherId] || [];
        const id = msg.message_id || msg._id;
        if (id && thread.some(m => (m.message_id || m._id) === id)) return prev;
        return { ...prev, [otherId]: [...thread, msg] };
      });
    } else {
      addMessageDeduped(setGroupMessages, msg);
    }
  };

  const handleNewDm = (msg) => {
    handleNewMessage(msg);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!newMessage.trim()) return;
    setSending(true);

    // Optimistically add own message immediately so sender sees it right away
    const optimisticMsg = {
      _id: `optimistic_${Date.now()}`,
      sender_id: user._id,
      sender_name: user.name,
      message: newMessage.trim(),
      dm_recipient_id: activeDmUserId || null,
      created_at: new Date().toISOString(),
    };

    if (activeDmUserId) {
      setDmMessages(prev => ({
        ...prev,
        [activeDmUserId]: [...(prev[activeDmUserId] || []), optimisticMsg],
      }));
    } else {
      setGroupMessages(prev => [...prev, optimisticMsg]);
    }

    const text = newMessage.trim();
    setNewMessage('');

    try {
      await chatAPI.sendMessage({
        project_id: projectId,
        message: text,
        ...(activeDmUserId ? { dm_recipient_id: activeDmUserId } : {}),
      });
    } catch {
      // Roll back optimistic message on failure
      if (activeDmUserId) {
        setDmMessages(prev => ({
          ...prev,
          [activeDmUserId]: (prev[activeDmUserId] || []).filter(m => m._id !== optimisticMsg._id),
        }));
      } else {
        setGroupMessages(prev => prev.filter(m => m._id !== optimisticMsg._id));
      }
      setNewMessage(text);
      alert('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleLeaveProject = async () => {
    try {
      const myCollab = team.team_members.find(m => m.user_id === user._id);
      if (myCollab) {
        await collaborationAPI.leaveProject(myCollab.collaboration_id);
        navigate('/dashboard');
      }
    } catch {
      alert('Failed to leave project');
    }
  };

  const handleRemoveMember = async (collaborationId) => {
    try {
      await collaborationAPI.removeMember(collaborationId);
      setConfirmRemove(null);
      await loadChatData();
    } catch {
      alert('Failed to remove member');
    }
  };

  // All members including founder for DM sidebar
  const allMembers = team ? [
    { ...team.founder, user_id: team.founder.user_id },
    ...(team.team_members || [])
  ] : [];

  const otherMembers = allMembers.filter(m => m.user_id !== user._id);

  const getDisplayName = (userId) => {
    const m = allMembers.find(m => m.user_id === userId);
    return m ? m.name : 'Unknown';
  };

  if (loading) {
    return (
      <div className="cinematic-loader" style={{ minHeight: '80vh' }}>
        <div style={{ position: 'relative', zIndex: 2, textAlign: 'center' }}>
          <div className="pulse-ring" style={{ margin: '0 auto 1rem auto' }} />
          <p className="mono-label">Loading chat</p>
        </div>
      </div>
    );
  }

  const totalMembers = 1 + (team?.team_members?.length || 0);
  const chatTitle = activeDmUserId
    ? `DM — ${getDisplayName(activeDmUserId)}`
    : `# ${team?.project?.title}`;

  return (
    <div style={{
      height: 'calc(100vh - 80px)',
      display: 'flex',
      maxWidth: '1400px',
      margin: '0 auto',
    }}>
      {/* ── Sidebar ── */}
      <div style={{
        width: '280px',
        flexShrink: 0,
        borderRight: `1px solid ${palette.colors.border.primary}`,
        display: 'flex',
        flexDirection: 'column',
        overflowY: 'auto',
      }}>
        {/* Project header */}
        <div style={{
          padding: palette.spacing.lg,
          borderBottom: `1px solid ${palette.colors.border.primary}`,
        }}>
          <h2 style={{ fontSize: palette.typography.fontSize.base, fontWeight: 600, marginBottom: 4 }}>
            {team?.project?.title}
          </h2>
          <p style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.secondary }}>
            {totalMembers} member{totalMembers !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Group chat button */}
        <div style={{ padding: `${palette.spacing.md} ${palette.spacing.lg} ${palette.spacing.sm}` }}>
          <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Channels</p>
          <button
            onClick={() => setChatMode('group')}
            style={{
              width: '100%',
              textAlign: 'left',
              background: chatMode === 'group' ? 'rgba(201,168,76,0.12)' : 'transparent',
              border: chatMode === 'group' ? `1px solid ${palette.colors.primary.cyan}` : '1px solid transparent',
              borderRadius: palette.borderRadius.md,
              padding: `${palette.spacing.sm} ${palette.spacing.md}`,
              color: chatMode === 'group' ? palette.colors.primary.cyan : palette.colors.text.secondary,
              fontFamily: palette.typography.fontFamily.primary,
              fontSize: palette.typography.fontSize.sm,
              cursor: 'pointer',
            }}
          >
            # Group Chat
          </button>
        </div>

        {/* DM section */}
        {otherMembers.length > 0 && (
          <div style={{ padding: `${palette.spacing.sm} ${palette.spacing.lg}` }}>
            <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Direct Messages</p>
            {otherMembers.map(member => {
              const dmKey = `dm_${member.user_id}`;
              const isActive = chatMode === dmKey;
              return (
                <button
                  key={member.user_id}
                  onClick={() => setChatMode(dmKey)}
                  style={{
                    width: '100%',
                    textAlign: 'left',
                    background: isActive ? 'rgba(201,168,76,0.12)' : 'transparent',
                    border: isActive ? `1px solid ${palette.colors.primary.cyan}` : '1px solid transparent',
                    borderRadius: palette.borderRadius.md,
                    padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                    color: isActive ? palette.colors.primary.cyan : palette.colors.text.secondary,
                    fontFamily: palette.typography.fontFamily.primary,
                    fontSize: palette.typography.fontSize.sm,
                    cursor: 'pointer',
                    marginBottom: 4,
                    display: 'flex',
                    alignItems: 'center',
                    gap: palette.spacing.sm,
                  }}
                >
                  <span style={{
                    width: 8, height: 8, borderRadius: '50%',
                    backgroundColor: member.is_founder ? palette.colors.primary.cyan : palette.colors.text.tertiary,
                    flexShrink: 0,
                  }} />
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {member.name}
                    {member.is_founder && <span style={{ fontSize: 10, color: palette.colors.primary.cyan }}> ★</span>}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {/* Team member management (visible in sidebar) */}
        <div style={{
          padding: `${palette.spacing.sm} ${palette.spacing.lg}`,
          flex: 1,
        }}>
          <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>Team Members</p>

          {/* Founder row */}
          <div style={{
            padding: `${palette.spacing.sm} ${palette.spacing.md}`,
            marginBottom: 4,
            borderRadius: palette.borderRadius.md,
            background: 'rgba(201,168,76,0.06)',
            fontSize: palette.typography.fontSize.xs,
          }}>
            <div style={{ fontWeight: 600, color: palette.colors.text.primary }}>{team?.founder.name}</div>
            <div style={{ color: palette.colors.primary.cyan, fontSize: 10, letterSpacing: '0.1em' }}>FOUNDER</div>
          </div>

          {/* Members */}
          {team?.team_members?.map(member => (
            <div key={member.user_id} style={{
              padding: `${palette.spacing.sm} ${palette.spacing.md}`,
              marginBottom: 4,
              borderRadius: palette.borderRadius.md,
              background: palette.colors.background.secondary,
              fontSize: palette.typography.fontSize.xs,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
            }}>
              <div>
                <div style={{ fontWeight: 500, color: palette.colors.text.primary }}>{member.name}</div>
                <div style={{ color: palette.colors.text.tertiary }}>{member.professional_title || 'Member'}</div>
              </div>
              {/* Founder can remove members */}
              {isFounder && member.user_id !== user._id && (
                <button
                  onClick={() => setConfirmRemove({ collaboration_id: member.collaboration_id, name: member.name })}
                  title="Remove member"
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: palette.colors.status.error,
                    cursor: 'pointer',
                    fontSize: 14,
                    lineHeight: 1,
                    padding: '2px 4px',
                  }}
                >
                  ✕
                </button>
              )}
            </div>
          ))}
        </div>

        {/* Bottom actions */}
        <div style={{
          padding: palette.spacing.md,
          borderTop: `1px solid ${palette.colors.border.primary}`,
          display: 'flex',
          flexDirection: 'column',
          gap: palette.spacing.sm,
        }}>
          {!isFounder && (
            confirmLeave ? (
              <div style={{ textAlign: 'center' }}>
                <p style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.secondary, marginBottom: palette.spacing.sm }}>
                  Are you sure?
                </p>
                <div style={{ display: 'flex', gap: palette.spacing.sm }}>
                  <Button variant="secondary" size="sm" fullWidth onClick={() => setConfirmLeave(false)}>Cancel</Button>
                  <Button size="sm" fullWidth onClick={handleLeaveProject} style={{ borderColor: palette.colors.status.error, color: palette.colors.status.error }}>Leave</Button>
                </div>
              </div>
            ) : (
              <Button variant="secondary" size="sm" fullWidth onClick={() => setConfirmLeave(true)}>
                Leave Project
              </Button>
            )
          )}
          <Button variant="outline" size="sm" fullWidth onClick={() => navigate('/dashboard')}>
            ← Dashboard
          </Button>
        </div>
      </div>

      {/* ── Main Chat ── */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        {/* Chat header */}
        <div style={{
          padding: `${palette.spacing.md} ${palette.spacing.xl}`,
          borderBottom: `1px solid ${palette.colors.border.primary}`,
          display: 'flex',
          alignItems: 'center',
          gap: palette.spacing.md,
        }}>
          <span style={{
            fontFamily: palette.typography.fontFamily.display,
            fontSize: palette.typography.fontSize.xl,
          }}>
            {chatTitle}
          </span>
          {activeDmUserId && (
            <span style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.tertiary }}>
              Private message
            </span>
          )}
        </div>

        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: `${palette.spacing.lg} ${palette.spacing.xl}`,
          display: 'flex',
          flexDirection: 'column',
          gap: palette.spacing.sm,
        }}>
          {currentMessages.length === 0 ? (
            <div style={{ textAlign: 'center', padding: palette.spacing['2xl'], color: palette.colors.text.tertiary }}>
              <p style={{ fontSize: '3rem', marginBottom: palette.spacing.md }}>💬</p>
              <p>{activeDmUserId ? `Start a private conversation with ${getDisplayName(activeDmUserId)}` : 'No messages yet. Start the conversation!'}</p>
            </div>
          ) : (
            currentMessages.map((message, index) => {
              const isOwn = message.sender_id === user._id;
              return (
                <div key={message._id || index} style={{
                  display: 'flex',
                  justifyContent: isOwn ? 'flex-end' : 'flex-start',
                }}>
                  <div style={{ maxWidth: '72%' }}>
                    {!isOwn && (
                      <p style={{
                        fontSize: palette.typography.fontSize.xs,
                        color: palette.colors.text.tertiary,
                        marginBottom: 4,
                        marginLeft: 4,
                      }}>
                        {message.sender_name}
                      </p>
                    )}
                    <div style={{
                      padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                      backgroundColor: isOwn
                        ? palette.colors.primary.cyan
                        : palette.colors.background.secondary,
                      color: isOwn
                        ? palette.colors.background.primary
                        : palette.colors.text.primary,
                      borderRadius: palette.borderRadius.lg,
                      fontSize: palette.typography.fontSize.sm,
                      lineHeight: 1.5,
                      wordBreak: 'break-word',
                    }}>
                      {message.message}
                    </div>
                    <p style={{
                      fontSize: 10,
                      color: palette.colors.text.tertiary,
                      marginTop: 2,
                      marginLeft: 4,
                      textAlign: isOwn ? 'right' : 'left',
                    }}>
                      {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <form onSubmit={handleSendMessage} style={{
          padding: `${palette.spacing.md} ${palette.spacing.xl}`,
          borderTop: `1px solid ${palette.colors.border.primary}`,
          display: 'flex',
          gap: palette.spacing.md,
          alignItems: 'center',
        }}>
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={activeDmUserId ? `Message ${getDisplayName(activeDmUserId)}…` : 'Message the team…'}
            disabled={sending}
            style={{
              flex: 1,
              padding: `${palette.spacing.sm} ${palette.spacing.md}`,
              backgroundColor: palette.colors.background.secondary,
              border: `1px solid ${palette.colors.border.primary}`,
              borderRadius: palette.borderRadius.md,
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              outline: 'none',
              fontFamily: palette.typography.fontFamily.primary,
            }}
            onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
            onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
          />
          <Button type="submit" loading={sending} disabled={!newMessage.trim()} size="md">
            Send
          </Button>
        </form>
      </div>

      {/* ── Remove member confirm modal ── */}
      {confirmRemove && (
        <div style={{
          position: 'fixed', inset: 0, zIndex: 9999,
          backgroundColor: 'rgba(0,0,0,0.7)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
        }}>
          <div className="surface-card" style={{
            borderRadius: palette.borderRadius.xl,
            padding: palette.spacing['2xl'],
            maxWidth: '420px',
            width: '90%',
            textAlign: 'center',
          }}>
            <h3 style={{
              fontFamily: palette.typography.fontFamily.display,
              fontSize: palette.typography.fontSize['2xl'],
              marginBottom: palette.spacing.md,
            }}>
              Remove {confirmRemove.name}?
            </h3>
            <p style={{ color: palette.colors.text.secondary, marginBottom: palette.spacing.xl, fontSize: palette.typography.fontSize.sm }}>
              They will be removed from the project and can no longer access the team chat.
            </p>
            <div style={{ display: 'flex', gap: palette.spacing.md, justifyContent: 'center' }}>
              <Button variant="secondary" onClick={() => setConfirmRemove(null)}>Cancel</Button>
              <Button
                onClick={() => handleRemoveMember(confirmRemove.collaboration_id)}
                style={{ borderColor: palette.colors.status.error, color: palette.colors.status.error }}
              >
                Remove
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LiveChat;