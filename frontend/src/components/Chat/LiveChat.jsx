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
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [team, setTeam] = useState(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadChatData();
    
    // Join project room for real-time messages
    if (socket) {
      joinProject(projectId);
      
      // Listen for new messages
      socket.on('new_message', handleNewMessage);
      socket.on('member_left', handleMemberLeft);
    }

    return () => {
      if (socket) {
        leaveProject(projectId);
        socket.off('new_message', handleNewMessage);
        socket.off('member_left', handleMemberLeft);
      }
    };
  }, [projectId, socket]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatData = async () => {
    try {
      // Load team info
      const teamResponse = await collaborationAPI.getTeamMembers(projectId);
      setTeam(teamResponse.data);

      // Load messages
      const messagesResponse = await chatAPI.getMessages(projectId);
      setMessages(messagesResponse.data.messages);
    } catch (error) {
      console.error('Error loading chat:', error);
      alert('Failed to load chat. You may not have access to this project.');
      navigate('/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleNewMessage = (messageData) => {
    setMessages(prev => [...prev, messageData]);
  };

  const handleMemberLeft = (data) => {
    // Reload team to update member list
    loadChatData();
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    
    if (!newMessage.trim()) return;

    setSending(true);
    try {
      await chatAPI.sendMessage({
        project_id: projectId,
        message: newMessage.trim()
      });
      setNewMessage('');
    } catch (error) {
      console.error('Error sending message:', error);
      alert('Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const handleLeaveProject = async () => {
    if (!window.confirm('Are you sure you want to leave this project?')) {
      return;
    }

    try {
      // Find user's collaboration
      const myCollaboration = team.team_members.find(m => m.user_id === user._id);
      if (myCollaboration) {
        await collaborationAPI.leaveProject(myCollaboration.collaboration_id);
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Error leaving project:', error);
      alert('Failed to leave project');
    }
  };

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        height: '80vh',
      }}>
        <div style={{
          width: '48px',
          height: '48px',
          border: `4px solid ${palette.colors.border.primary}`,
          borderTop: `4px solid ${palette.colors.primary.cyan}`,
          borderRadius: '50%',
          animation: 'spin 1s linear infinite',
        }}></div>
      </div>
    );
  }

  const isFounder = team && team.founder.user_id === user._id;
  const totalMembers = 1 + (team?.team_members?.length || 0);

  return (
    <div style={{
      height: 'calc(100vh - 80px)',
      display: 'flex',
      maxWidth: '1400px',
      margin: '0 auto',
    }}>
      {/* Sidebar - Team Members */}
      <div style={{
        width: '300px',
        borderRight: `1px solid ${palette.colors.border.primary}`,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Project Header */}
        <div style={{
          padding: palette.spacing.xl,
          borderBottom: `1px solid ${palette.colors.border.primary}`,
        }}>
          <h2 style={{
            fontSize: palette.typography.fontSize.xl,
            fontWeight: palette.typography.fontWeight.bold,
            marginBottom: palette.spacing.xs,
          }}>
            {team?.project?.title}
          </h2>
          <p style={{
            fontSize: palette.typography.fontSize.sm,
            color: palette.colors.text.secondary,
          }}>
            {totalMembers} member{totalMembers !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Team List */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: palette.spacing.md,
        }}>
          {/* Founder */}
          <div style={{
            padding: palette.spacing.md,
            marginBottom: palette.spacing.sm,
            backgroundColor: 'rgba(19, 239, 183, 0.1)',
            borderRadius: palette.borderRadius.md,
          }}>
            <div style={{
              fontSize: palette.typography.fontSize.sm,
              fontWeight: palette.typography.fontWeight.semibold,
              marginBottom: palette.spacing.xs,
            }}>
              {team?.founder.name}
            </div>
            <div style={{
              fontSize: palette.typography.fontSize.xs,
              color: palette.colors.primary.cyan,
            }}>
              Founder
            </div>
          </div>

          {/* Members */}
          {team?.team_members?.map((member) => (
            <div
              key={member.user_id}
              style={{
                padding: palette.spacing.md,
                marginBottom: palette.spacing.sm,
                backgroundColor: palette.colors.background.secondary,
                borderRadius: palette.borderRadius.md,
              }}
            >
              <div style={{
                fontSize: palette.typography.fontSize.sm,
                fontWeight: palette.typography.fontWeight.medium,
                marginBottom: palette.spacing.xs,
              }}>
                {member.name}
              </div>
              <div style={{
                fontSize: palette.typography.fontSize.xs,
                color: palette.colors.text.secondary,
              }}>
                {member.professional_title || 'Team Member'}
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div style={{
          padding: palette.spacing.md,
          borderTop: `1px solid ${palette.colors.border.primary}`,
        }}>
          {!isFounder && (
            <Button
              variant="secondary"
              size="sm"
              fullWidth
              onClick={handleLeaveProject}
            >
              Leave Project
            </Button>
          )}
          <Button
            variant="outline"
            size="sm"
            fullWidth
            onClick={() => navigate('/dashboard')}
            style={{ marginTop: palette.spacing.sm }}
          >
            Back to Dashboard
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Messages */}
        <div style={{
          flex: 1,
          overflowY: 'auto',
          padding: palette.spacing.xl,
          display: 'flex',
          flexDirection: 'column',
          gap: palette.spacing.md,
        }}>
          {messages.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: palette.spacing['3xl'],
              color: palette.colors.text.secondary,
            }}>
              <div style={{ fontSize: '64px', marginBottom: palette.spacing.lg }}>💬</div>
              <p>No messages yet. Start the conversation!</p>
            </div>
          ) : (
            messages.map((message, index) => {
              const isOwnMessage = message.sender_id === user._id;
              return (
                <div
                  key={message._id || index}
                  style={{
                    display: 'flex',
                    justifyContent: isOwnMessage ? 'flex-end' : 'flex-start',
                  }}
                >
                  <div style={{
                    maxWidth: '70%',
                  }}>
                    {!isOwnMessage && (
                      <div style={{
                        fontSize: palette.typography.fontSize.xs,
                        color: palette.colors.text.tertiary,
                        marginBottom: palette.spacing.xs,
                        marginLeft: palette.spacing.sm,
                      }}>
                        {message.sender_name}
                      </div>
                    )}
                    <div style={{
                      padding: palette.spacing.md,
                      backgroundColor: isOwnMessage 
                        ? palette.colors.primary.cyan
                        : palette.colors.background.secondary,
                      color: isOwnMessage 
                        ? palette.colors.background.primary
                        : palette.colors.text.primary,
                      borderRadius: palette.borderRadius.lg,
                      wordWrap: 'break-word',
                    }}>
                      {message.message}
                    </div>
                    <div style={{
                      fontSize: palette.typography.fontSize.xs,
                      color: palette.colors.text.tertiary,
                      marginTop: palette.spacing.xs,
                      marginLeft: palette.spacing.sm,
                    }}>
                      {new Date(message.created_at).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Message Input */}
        <form onSubmit={handleSendMessage} style={{
          padding: palette.spacing.xl,
          borderTop: `1px solid ${palette.colors.border.primary}`,
          display: 'flex',
          gap: palette.spacing.md,
        }}>
          <input
            type="text"
            value={newMessage}
            onChange={(e) => setNewMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={sending}
            style={{
              flex: 1,
              padding: palette.spacing.md,
              backgroundColor: palette.colors.background.secondary,
              border: `1px solid ${palette.colors.border.primary}`,
              borderRadius: palette.borderRadius.md,
              color: palette.colors.text.primary,
              fontSize: palette.typography.fontSize.base,
              outline: 'none',
            }}
            onFocus={(e) => e.target.style.borderColor = palette.colors.primary.cyan}
            onBlur={(e) => e.target.style.borderColor = palette.colors.border.primary}
          />
          <Button type="submit" loading={sending} disabled={!newMessage.trim()}>
            Send
          </Button>
        </form>
      </div>
    </div>
  );
};

export default LiveChat;