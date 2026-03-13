import React, { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import palette from "../../palette";
import { chatAPI, collaborationAPI } from "../../services/api";
import { useWebSocket } from "../../utils/websocket";
import Button from "../Common/Button";

const notify = (type, message) => {
  window.dispatchEvent(new CustomEvent("app-toast", { detail: { type, message } }));
};

const LiveChat = ({ user }) => {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { socket, joinProject, leaveProject } = useWebSocket();

  const [chatMode, setChatMode] = useState("group");
  const [groupMessages, setGroupMessages] = useState([]);
  const [dmMessages, setDmMessages] = useState({});
  const [newMessage, setNewMessage] = useState("");
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [confirmLeave, setConfirmLeave] = useState(false);
  const [confirmRemove, setConfirmRemove] = useState(null);
  const [unreadThreads, setUnreadThreads] = useState({ group: 0, dms: {} });
  const [groupPaging, setGroupPaging] = useState({ next_before: null, limit: 50 });
  const [dmPaging, setDmPaging] = useState({});
  const messagesEndRef = useRef(null);

  const isFounder = team && team.founder.user_id === user._id;
  const activeDmUserId = chatMode.startsWith("dm_") ? chatMode.replace("dm_", "") : null;
  const currentMessages = activeDmUserId ? dmMessages[activeDmUserId] || [] : groupMessages;

  const allMembers = useMemo(() => {
    if (!team) return [];
    return [{ ...team.founder, user_id: team.founder.user_id }, ...(team.team_members || [])];
  }, [team]);

  const otherMembers = allMembers.filter((m) => m.user_id !== user._id);

  useEffect(() => {
    loadChatData();
  }, [projectId]);

  useEffect(() => {
    if (!socket) return;
    joinProject(projectId);
    socket.on("new_message", handleIncomingMessage);
    socket.on("new_dm", handleIncomingMessage);
    socket.on("member_left", () => loadTeamOnly());
    return () => {
      leaveProject(projectId);
      socket.off("new_message", handleIncomingMessage);
      socket.off("new_dm", handleIncomingMessage);
      socket.off("member_left");
    };
  }, [socket, projectId, activeDmUserId]);

  useEffect(() => {
    if (!socket || !activeDmUserId) return;
    socket.emit("join_dm", { other_user_id: activeDmUserId, token: localStorage.getItem("token") });
    if (!dmMessages[activeDmUserId]) {
      chatAPI
        .getDMMessages(projectId, activeDmUserId, { limit: 50 })
        .then((r) => {
          setDmMessages((prev) => ({ ...prev, [activeDmUserId]: r.data.messages || [] }));
          setDmPaging((prev) => ({ ...prev, [activeDmUserId]: r.data.paging || { next_before: null, limit: 50 } }));
        })
        .catch(() => {});
    }
    return () => {
      socket.emit("leave_dm", { other_user_id: activeDmUserId, token: localStorage.getItem("token") });
    };
  }, [socket, activeDmUserId, projectId]);

  useEffect(() => {
    if (chatMode === "group") {
      setUnreadThreads((prev) => ({ ...prev, group: 0 }));
    } else if (activeDmUserId) {
      setUnreadThreads((prev) => ({
        ...prev,
        dms: { ...(prev.dms || {}), [activeDmUserId]: 0 },
      }));
    }
  }, [chatMode, activeDmUserId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentMessages.length, activeDmUserId]);

  const loadTeamOnly = async () => {
    const teamRes = await collaborationAPI.getTeamMembers(projectId);
    setTeam(teamRes.data);
  };

  const loadChatData = async () => {
    setLoading(true);
    try {
      const [teamRes, msgRes, unreadRes] = await Promise.all([
        collaborationAPI.getTeamMembers(projectId),
        chatAPI.getMessages(projectId, { limit: 50 }),
        chatAPI.getUnreadCount(projectId),
      ]);
      setTeam(teamRes.data);
      setGroupMessages(msgRes.data.messages || []);
      setGroupPaging(msgRes.data.paging || { next_before: null, limit: 50 });
      setUnreadThreads(unreadRes.data.threads || { group: 0, dms: {} });
    } catch {
      notify("error", "Failed to load chat. You may not have access to this project.");
      navigate("/dashboard");
    } finally {
      setLoading(false);
    }
  };

  const addOrReconcile = (prev, msg) => {
    const serverId = msg.message_id || msg._id;
    const clientId = msg.client_message_id;

    if (serverId && prev.some((m) => (m.message_id || m._id) === serverId)) return prev;

    if (clientId) {
      const idx = prev.findIndex((m) => m.client_message_id && m.client_message_id === clientId);
      if (idx >= 0) {
        const next = [...prev];
        next[idx] = { ...next[idx], ...msg, _id: serverId || next[idx]._id };
        return next;
      }
    }

    return [...prev, msg];
  };

  const handleIncomingMessage = (msg) => {
    if (msg.dm_recipient_id) {
      const otherId = msg.sender_id === user._id ? msg.dm_recipient_id : msg.sender_id;
      setDmMessages((prev) => ({ ...prev, [otherId]: addOrReconcile(prev[otherId] || [], msg) }));
      if (msg.sender_id !== user._id) {
        setUnreadThreads((prev) => ({
          ...prev,
          dms: { ...(prev.dms || {}), [otherId]: ((prev.dms || {})[otherId] || 0) + 1 },
        }));
      }
      return;
    }
    setGroupMessages((prev) => addOrReconcile(prev, msg));
    if (msg.sender_id !== user._id && !activeDmUserId) {
      setUnreadThreads((prev) => ({ ...prev, group: (prev.group || 0) + 1 }));
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    const text = newMessage.trim();
    if (!text) return;
    setSending(true);

    const clientMessageId = `c_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    const optimisticMessage = {
      _id: `optimistic_${clientMessageId}`,
      client_message_id: clientMessageId,
      sender_id: user._id,
      sender_name: user.name,
      message: text,
      dm_recipient_id: activeDmUserId || null,
      created_at: new Date().toISOString(),
    };

    if (activeDmUserId) {
      setDmMessages((prev) => ({ ...prev, [activeDmUserId]: [...(prev[activeDmUserId] || []), optimisticMessage] }));
    } else {
      setGroupMessages((prev) => [...prev, optimisticMessage]);
    }
    setNewMessage("");

    try {
      await chatAPI.sendMessage({
        project_id: projectId,
        message: text,
        client_message_id: clientMessageId,
        ...(activeDmUserId ? { dm_recipient_id: activeDmUserId } : {}),
      });
    } catch {
      if (activeDmUserId) {
        setDmMessages((prev) => ({
          ...prev,
          [activeDmUserId]: (prev[activeDmUserId] || []).filter((m) => m.client_message_id !== clientMessageId),
        }));
      } else {
        setGroupMessages((prev) => prev.filter((m) => m.client_message_id !== clientMessageId));
      }
      setNewMessage(text);
      notify("error", "Failed to send message");
    } finally {
      setSending(false);
    }
  };

  const loadOlder = async () => {
    try {
      if (activeDmUserId) {
        const paging = dmPaging[activeDmUserId];
        if (!paging?.next_before) return;
        const r = await chatAPI.getDMMessages(projectId, activeDmUserId, {
          limit: paging.limit || 50,
          before: paging.next_before,
        });
        setDmMessages((prev) => ({ ...prev, [activeDmUserId]: [...(r.data.messages || []), ...(prev[activeDmUserId] || [])] }));
        setDmPaging((prev) => ({ ...prev, [activeDmUserId]: r.data.paging || paging }));
      } else {
        if (!groupPaging?.next_before) return;
        const r = await chatAPI.getMessages(projectId, { limit: groupPaging.limit || 50, before: groupPaging.next_before });
        setGroupMessages((prev) => [...(r.data.messages || []), ...prev]);
        setGroupPaging(r.data.paging || groupPaging);
      }
    } catch {
      notify("warning", "Could not load older messages");
    }
  };

  const handleLeaveProject = async () => {
    try {
      const myCollab = team.team_members.find((m) => m.user_id === user._id);
      if (myCollab) {
        await collaborationAPI.leaveProject(myCollab.collaboration_id);
        navigate("/dashboard");
      }
    } catch {
      notify("error", "Failed to leave project");
    }
  };

  const handleRemoveMember = async (collaborationId) => {
    try {
      await collaborationAPI.removeMember(collaborationId);
      setConfirmRemove(null);
      await loadTeamOnly();
    } catch {
      notify("error", "Failed to remove member");
    }
  };

  const getDisplayName = (userId) => {
    const member = allMembers.find((m) => m.user_id === userId);
    return member ? member.name : "Unknown";
  };

  if (loading) {
    return (
      <div className="cinematic-loader" style={{ minHeight: "80vh" }}>
        <div style={{ position: "relative", zIndex: 2, textAlign: "center" }}>
          <div className="pulse-ring" style={{ margin: "0 auto 1rem auto" }} />
          <p className="mono-label">Loading chat</p>
        </div>
      </div>
    );
  }

  const totalMembers = 1 + (team?.team_members?.length || 0);
  const chatTitle = activeDmUserId ? `DM - ${getDisplayName(activeDmUserId)}` : `# ${team?.project?.title}`;
  const canLoadMore = activeDmUserId ? !!dmPaging[activeDmUserId]?.next_before : !!groupPaging?.next_before;

  return (
    <div style={{ height: "calc(100vh - 80px)", display: "flex", maxWidth: "1400px", margin: "0 auto" }}>
      <div
        style={{
          width: "280px",
          flexShrink: 0,
          borderRight: `1px solid ${palette.colors.border.primary}`,
          display: "flex",
          flexDirection: "column",
          overflowY: "auto",
        }}
      >
        <div style={{ padding: palette.spacing.lg, borderBottom: `1px solid ${palette.colors.border.primary}` }}>
          <h2 style={{ fontSize: palette.typography.fontSize.base, fontWeight: 600, marginBottom: 4 }}>{team?.project?.title}</h2>
          <p style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.secondary }}>
            {totalMembers} member{totalMembers !== 1 ? "s" : ""}
          </p>
        </div>

        <div style={{ padding: `${palette.spacing.md} ${palette.spacing.lg} ${palette.spacing.sm}` }}>
          <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>
            Channels
          </p>
          <button
            onClick={() => setChatMode("group")}
            style={{
              width: "100%",
              textAlign: "left",
              background: chatMode === "group" ? "rgba(201,168,76,0.12)" : "transparent",
              border: chatMode === "group" ? `1px solid ${palette.colors.primary.cyan}` : "1px solid transparent",
              borderRadius: palette.borderRadius.md,
              padding: `${palette.spacing.sm} ${palette.spacing.md}`,
              color: chatMode === "group" ? palette.colors.primary.cyan : palette.colors.text.secondary,
              fontFamily: palette.typography.fontFamily.primary,
              fontSize: palette.typography.fontSize.sm,
              cursor: "pointer",
            }}
          >
            # Group Chat
            {!!unreadThreads.group && (
              <span style={{ marginLeft: 8, fontSize: 10, color: palette.colors.primary.cyan }}>
                ({unreadThreads.group})
              </span>
            )}
          </button>
        </div>

        {otherMembers.length > 0 && (
          <div style={{ padding: `${palette.spacing.sm} ${palette.spacing.lg}` }}>
            <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>
              Direct Messages
            </p>
            {otherMembers.map((member) => {
              const dmKey = `dm_${member.user_id}`;
              const isActive = chatMode === dmKey;
              return (
                <button
                  key={member.user_id}
                  onClick={() => setChatMode(dmKey)}
                  style={{
                    width: "100%",
                    textAlign: "left",
                    background: isActive ? "rgba(201,168,76,0.12)" : "transparent",
                    border: isActive ? `1px solid ${palette.colors.primary.cyan}` : "1px solid transparent",
                    borderRadius: palette.borderRadius.md,
                    padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                    color: isActive ? palette.colors.primary.cyan : palette.colors.text.secondary,
                    fontFamily: palette.typography.fontFamily.primary,
                    fontSize: palette.typography.fontSize.sm,
                    cursor: "pointer",
                    marginBottom: 4,
                    display: "flex",
                    alignItems: "center",
                    gap: palette.spacing.sm,
                  }}
                >
                  <span
                    style={{
                      width: 8,
                      height: 8,
                      borderRadius: "50%",
                      backgroundColor: member.is_founder ? palette.colors.primary.cyan : palette.colors.text.tertiary,
                      flexShrink: 0,
                    }}
                  />
                  <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {member.name}
                    {member.is_founder && <span style={{ fontSize: 10, color: palette.colors.primary.cyan }}> *</span>}
                    {!!unreadThreads?.dms?.[member.user_id] && (
                      <span style={{ marginLeft: 6, fontSize: 10, color: palette.colors.primary.cyan }}>
                        ({unreadThreads.dms[member.user_id]})
                      </span>
                    )}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        <div style={{ padding: `${palette.spacing.sm} ${palette.spacing.lg}`, flex: 1 }}>
          <p className="mono-label" style={{ marginBottom: palette.spacing.sm }}>
            Team Members
          </p>
          <div
            style={{
              padding: `${palette.spacing.sm} ${palette.spacing.md}`,
              marginBottom: 4,
              borderRadius: palette.borderRadius.md,
              background: "rgba(201,168,76,0.06)",
              fontSize: palette.typography.fontSize.xs,
            }}
          >
            <div style={{ fontWeight: 600, color: palette.colors.text.primary }}>{team?.founder.name}</div>
            <div style={{ color: palette.colors.primary.cyan, fontSize: 10, letterSpacing: "0.1em" }}>FOUNDER</div>
          </div>

          {team?.team_members?.map((member) => (
            <div
              key={member.user_id}
              style={{
                padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                marginBottom: 4,
                borderRadius: palette.borderRadius.md,
                background: palette.colors.background.secondary,
                fontSize: palette.typography.fontSize.xs,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              <div>
                <div style={{ fontWeight: 500, color: palette.colors.text.primary }}>{member.name}</div>
                <div style={{ color: palette.colors.text.tertiary }}>{member.professional_title || "Member"}</div>
              </div>
              {isFounder && member.user_id !== user._id && (
                <button
                  onClick={() => setConfirmRemove({ collaboration_id: member.collaboration_id, name: member.name })}
                  title="Remove member"
                  style={{
                    background: "transparent",
                    border: "none",
                    color: palette.colors.status.error,
                    cursor: "pointer",
                    fontSize: 14,
                    lineHeight: 1,
                    padding: "2px 4px",
                  }}
                >
                  X
                </button>
              )}
            </div>
          ))}
        </div>

        <div
          style={{
            padding: palette.spacing.md,
            borderTop: `1px solid ${palette.colors.border.primary}`,
            display: "flex",
            flexDirection: "column",
            gap: palette.spacing.sm,
          }}
        >
          {!isFounder &&
            (confirmLeave ? (
              <div style={{ textAlign: "center" }}>
                <p
                  style={{
                    fontSize: palette.typography.fontSize.xs,
                    color: palette.colors.text.secondary,
                    marginBottom: palette.spacing.sm,
                  }}
                >
                  Are you sure?
                </p>
                <div style={{ display: "flex", gap: palette.spacing.sm }}>
                  <Button variant="secondary" size="sm" fullWidth onClick={() => setConfirmLeave(false)}>
                    Cancel
                  </Button>
                  <Button size="sm" fullWidth onClick={handleLeaveProject} style={{ borderColor: palette.colors.status.error, color: palette.colors.status.error }}>
                    Leave
                  </Button>
                </div>
              </div>
            ) : (
              <Button variant="secondary" size="sm" fullWidth onClick={() => setConfirmLeave(true)}>
                Leave Project
              </Button>
            ))}
          <Button variant="outline" size="sm" fullWidth onClick={() => navigate("/dashboard")}>
            Back to Dashboard
          </Button>
        </div>
      </div>

      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        <div
          style={{
            padding: `${palette.spacing.md} ${palette.spacing.xl}`,
            borderBottom: `1px solid ${palette.colors.border.primary}`,
            display: "flex",
            alignItems: "center",
            gap: palette.spacing.md,
          }}
        >
          <span style={{ fontFamily: palette.typography.fontFamily.display, fontSize: palette.typography.fontSize.xl }}>{chatTitle}</span>
          {activeDmUserId && <span style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.tertiary }}>Private message</span>}
        </div>

        <div
          style={{
            flex: 1,
            overflowY: "auto",
            padding: `${palette.spacing.lg} ${palette.spacing.xl}`,
            display: "flex",
            flexDirection: "column",
            gap: palette.spacing.sm,
          }}
        >
          {canLoadMore && (
            <div style={{ textAlign: "center" }}>
              <Button size="sm" variant="secondary" onClick={loadOlder}>
                Load older messages
              </Button>
            </div>
          )}

          {currentMessages.length === 0 ? (
            <div style={{ textAlign: "center", padding: palette.spacing["2xl"], color: palette.colors.text.tertiary }}>
              <p style={{ fontSize: "2rem", marginBottom: palette.spacing.md }}>Chat</p>
              <p>
                {activeDmUserId
                  ? `Start a private conversation with ${getDisplayName(activeDmUserId)}`
                  : "No messages yet. Start the conversation."}
              </p>
            </div>
          ) : (
            currentMessages.map((message, index) => {
              const isOwn = message.sender_id === user._id;
              return (
                <div key={message.message_id || message._id || index} style={{ display: "flex", justifyContent: isOwn ? "flex-end" : "flex-start" }}>
                  <div style={{ maxWidth: "72%" }}>
                    {!isOwn && (
                      <p style={{ fontSize: palette.typography.fontSize.xs, color: palette.colors.text.tertiary, marginBottom: 4, marginLeft: 4 }}>
                        {message.sender_name}
                      </p>
                    )}
                    <div
                      style={{
                        padding: `${palette.spacing.sm} ${palette.spacing.md}`,
                        backgroundColor: isOwn ? palette.colors.primary.cyan : palette.colors.background.secondary,
                        color: isOwn ? palette.colors.background.primary : palette.colors.text.primary,
                        borderRadius: palette.borderRadius.lg,
                        fontSize: palette.typography.fontSize.sm,
                        lineHeight: 1.5,
                        wordBreak: "break-word",
                        opacity: message._id?.startsWith("optimistic_") ? 0.7 : 1,
                      }}
                    >
                      {message.message}
                    </div>
                    <p
                      style={{
                        fontSize: 10,
                        color: palette.colors.text.tertiary,
                        marginTop: 2,
                        marginLeft: 4,
                        textAlign: isOwn ? "right" : "left",
                      }}
                    >
                      {new Date(message.created_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                    </p>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        <form
          onSubmit={handleSendMessage}
          style={{
            padding: `${palette.spacing.md} ${palette.spacing.xl}`,
            borderTop: `1px solid ${palette.colors.border.primary}`,
            display: "flex",
            gap: palette.spacing.md,
            alignItems: "center",
          }}
        >
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder={activeDmUserId ? `Message ${getDisplayName(activeDmUserId)}...` : "Message the team..."}
            disabled={sending}
            style={{
              flex: 1,
              padding: `${palette.spacing.sm} ${palette.spacing.md}`,
              backgroundColor: palette.colors.background.secondary,
              border: `1px solid ${palette.colors.border.primary}`,
              borderRadius: palette.borderRadius.md,
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.sm,
              outline: "none",
              fontFamily: palette.typography.fontFamily.primary,
            }}
            onFocus={(e) => (e.target.style.borderColor = palette.colors.primary.cyan)}
            onBlur={(e) => (e.target.style.borderColor = palette.colors.border.primary)}
          />
          <Button type="submit" loading={sending} disabled={!newMessage.trim()} size="md">
            Send
          </Button>
        </form>
      </div>

      {confirmRemove && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            zIndex: 9999,
            backgroundColor: "rgba(0,0,0,0.7)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <div
            className="surface-card"
            style={{
              borderRadius: palette.borderRadius.xl,
              padding: palette.spacing["2xl"],
              maxWidth: "420px",
              width: "90%",
              textAlign: "center",
            }}
          >
            <h3
              style={{
                fontFamily: palette.typography.fontFamily.display,
                fontSize: palette.typography.fontSize["2xl"],
                marginBottom: palette.spacing.md,
              }}
            >
              Remove {confirmRemove.name}?
            </h3>
            <p style={{ color: palette.colors.text.secondary, marginBottom: palette.spacing.xl, fontSize: palette.typography.fontSize.sm }}>
              They will be removed from the project and can no longer access the team chat.
            </p>
            <div style={{ display: "flex", gap: palette.spacing.md, justifyContent: "center" }}>
              <Button variant="secondary" onClick={() => setConfirmRemove(null)}>
                Cancel
              </Button>
              <Button onClick={() => handleRemoveMember(confirmRemove.collaboration_id)} style={{ borderColor: palette.colors.status.error, color: palette.colors.status.error }}>
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
