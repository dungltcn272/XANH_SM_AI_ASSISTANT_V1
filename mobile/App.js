import React, { useState, useEffect, useRef } from 'react';
import { 
  StyleSheet, Text, View, TextInput, TouchableOpacity, SafeAreaView, 
  StatusBar, ScrollView, KeyboardAvoidingView, Platform, Image, Keyboard, Animated,
  Alert, Modal, Linking, Dimensions, TouchableWithoutFeedback, ImageBackground
} from 'react-native';
import { Ionicons, Feather, MaterialCommunityIcons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';
import { LinearGradient } from 'expo-linear-gradient';
import * as ImagePicker from 'expo-image-picker';
import Markdown from 'react-native-markdown-display';
import * as WebBrowser from 'expo-web-browser';
import * as Google from 'expo-auth-session/providers/google';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LogBox } from 'react-native';
import { Image as ExpoImage } from 'expo-image';

LogBox.ignoreLogs(['A props object containing a "key" prop is being spread into JSX']);

WebBrowser.maybeCompleteAuthSession();

const API_BASE = 'https://ragxanhsmv1-production.up.railway.app/api';
const { width } = Dimensions.get('window');

export default function App() {
  const [inputText, setInputText] = useState('');
  const [messages, setMessages] = useState([]);
  const [attachedImage, setAttachedImage] = useState(null);
  const [token, setToken] = useState(null);
  const [loadingToken, setLoadingToken] = useState(true);
  const [isDeepSearch, setIsDeepSearch] = useState(false);

  // History States
  const [conversations, setConversations] = useState([]);
  const [activeConversationId, setActiveConversationId] = useState(null);

  // Theme State
  const [theme, setTheme] = useState('dark');

  // Review & Feedback States
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [feedbackMessageId, setFeedbackMessageId] = useState(null);
  const [feedbackTags, setFeedbackTags] = useState([]);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [submittedReviews, setSubmittedReviews] = useState({});
  const [submittingReview, setSubmittingReview] = useState(false);

  // Header Interactive States
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isNotifOpen, setIsNotifOpen] = useState(false);
  const [isUserModalOpen, setIsUserModalOpen] = useState(false);
  const [isLoggedInGG, setIsLoggedInGG] = useState(false);
  const [ggLoading, setGgLoading] = useState(false);
  const [userInfo, setUserInfo] = useState(null);
  
  const drawerAnim = useRef(new Animated.Value(-width)).current;
  const scrollViewRef = useRef();
  const textInputRef = useRef();

  // Animations
  const floatAnim = useRef(new Animated.Value(0)).current;
  const botAvatarFloatAnim = useRef(new Animated.Value(0)).current;

  // Google Auth
  const [request, response, promptAsync] = Google.useIdTokenAuthRequest({
    clientId: '906649545945-2vaj1jnl8vu9t700f4kd0a2otlro8u91.apps.googleusercontent.com',
    iosClientId: '906649545945-hitv4m3ch6op4ht1osfh215ih7doq2ma.apps.googleusercontent.com',
    androidClientId: '906649545945-popcj1hf8k0r3lgvh1ao7h0aa48lgkce.apps.googleusercontent.com',
  });

  // Start Animations
  useEffect(() => {
    Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, { toValue: -15, duration: 1500, useNativeDriver: true }),
        Animated.timing(floatAnim, { toValue: 0, duration: 1500, useNativeDriver: true })
      ])
    ).start();

    Animated.loop(
      Animated.sequence([
        Animated.timing(botAvatarFloatAnim, { toValue: -5, duration: 800, useNativeDriver: true }),
        Animated.timing(botAvatarFloatAnim, { toValue: 0, duration: 800, useNativeDriver: true })
      ])
    ).start();
  }, [floatAnim, botAvatarFloatAnim]);

  // Initial Login logic
  useEffect(() => {
    const initApp = async () => {
      try {
        const savedTheme = await AsyncStorage.getItem('app_theme');
        if (savedTheme) setTheme(savedTheme);

        const savedToken = await AsyncStorage.getItem('app_token');
        if (savedToken) {
          setToken(savedToken);
          setIsLoggedInGG(true);
          fetchConversations(savedToken);
          setUserInfo({ name: 'User', initial: 'U' });
        } else {
          loginGuest();
        }
      } catch(e) { loginGuest(); }
      finally { setLoadingToken(false); }
    };
    initApp();
  }, []);

  const loginGuest = async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/guest`, { method: 'POST' });
      const data = await res.json();
      setToken(data.access_token);
    } catch (err) {}
  };

  const fetchConversations = async (useToken) => {
    try {
      const res = await fetch(`${API_BASE}/conversations`, {
        headers: { "Authorization": `Bearer ${useToken || token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data);
      }
    } catch(e) { console.error("Error fetching conversations", e); }
  };

  const loadConversation = async (id) => {
    try {
      setActiveConversationId(id);
      setIsDrawerOpen(false);
      Animated.timing(drawerAnim, { toValue: -width, duration: 300, useNativeDriver: true }).start();
      
      const res = await fetch(`${API_BASE}/conversations/${id}/messages`, {
        headers: { "Authorization": `Bearer ${token}` }
      });
      if (res.ok) {
        const msgs = await res.json();
        setMessages(msgs.map(m => ({
          id: m.id || m.message_id || Math.random().toString(),
          text: m.content,
          isUser: m.role === 'user',
          sources: m.sources,
          latency_ms: m.latency_ms
        })));
      }
    } catch(e) {}
  };

  const startNewChat = () => {
    setActiveConversationId(null);
    setMessages([]);
    setIsDrawerOpen(false);
    Animated.timing(drawerAnim, { toValue: -width, duration: 300, useNativeDriver: true }).start();
  };

  // Google Login Effect
  useEffect(() => {
    if (response?.type === 'success') {
      const { id_token } = response.params;
      if (id_token) {
        handleBackendLogin(id_token);
      }
    } else if (response?.type === 'error' || response?.type === 'dismiss') {
      setGgLoading(false);
      if (Platform.OS === 'ios') {
        Alert.alert(
          'Giới hạn của Google',
          'Google chặn đường dẫn thử nghiệm của Expo Go trên iOS. Để tiếp tục test UI và Lịch sử Chat, bạn có muốn dùng tài khoản Demo không?',
          [
            { text: 'Hủy', style: 'cancel' },
            { text: 'Đăng nhập Demo', onPress: () => {
                setToken('mock_token_for_ui_test');
                setIsLoggedInGG(true);
                setUserInfo({
                  name: 'Dũng Nguyễn (Demo)',
                  email: 'dung.demo@gmail.com',
                  picture: 'https://lh3.googleusercontent.com/a/default-user',
                  initial: 'D'
                });
                setIsUserModalOpen(false);
            }}
          ]
        );
      } else {
        if (response?.type === 'error') Alert.alert('Lỗi', 'Đăng nhập Google thất bại');
      }
    }
  }, [response]);

  const handleBackendLogin = async (id_token) => {
    try {
      setGgLoading(true);
      const res = await fetch(`${API_BASE}/auth/google`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: id_token }),
      });
      const data = await res.json();
      if (res.ok) {
        setToken(data.access_token);
        setIsLoggedInGG(true);
        await AsyncStorage.setItem('app_token', data.access_token);
        fetchConversations(data.access_token);

        const userInfoRes = await fetch(`https://www.googleapis.com/oauth2/v3/tokeninfo?id_token=${id_token}`);
        if (userInfoRes.ok) {
          const googleUser = await userInfoRes.json();
          setUserInfo({
            name: googleUser.name,
            email: googleUser.email,
            picture: googleUser.picture,
            initial: googleUser.name ? googleUser.name.charAt(0).toUpperCase() : 'U'
          });
        }
      }
    } catch(err) {} 
    finally {
      setGgLoading(false);
      setIsUserModalOpen(false);
    }
  };

  const handleGGLogin = () => {
    setGgLoading(true);
    promptAsync();
  };

  const handleLogout = async () => {
    setToken(null);
    setIsLoggedInGG(false);
    setUserInfo(null);
    setConversations([]);
    setActiveConversationId(null);
    setMessages([]);
    setIsUserModalOpen(false);
    setIsDrawerOpen(false);
    Animated.timing(drawerAnim, { toValue: -width, duration: 300, useNativeDriver: true }).start();
    await AsyncStorage.removeItem('app_token');
    loginGuest();
  };

  // Toggle Nav Drawer
  const toggleDrawer = () => {
    if (isDrawerOpen) {
      Animated.timing(drawerAnim, { toValue: -width, duration: 300, useNativeDriver: true }).start(() => setIsDrawerOpen(false));
    } else {
      setIsDrawerOpen(true);
      Animated.timing(drawerAnim, { toValue: 0, duration: 300, useNativeDriver: true }).start();
    }
  };

  const handleToggleTheme = async (val) => {
    const newTheme = val ? 'dark' : 'light';
    setTheme(newTheme);
    await AsyncStorage.setItem('app_theme', newTheme);
  };

  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') return alert('Cần cấp quyền Thư viện');
    let result = await ImagePicker.launchImageLibraryAsync({ base64: true, quality: 0.5 });
    if (!result.canceled) setAttachedImage({ uri: result.assets[0].uri, base64: result.assets[0].base64 });
  };

  const handleReviewClick = (messageId, type) => {
    if (type === 'up') setSubmittedReviews(prev => ({ ...prev, [messageId]: 'up' }));
    else {
      setFeedbackMessageId(messageId);
      setFeedbackTags([]);
      setFeedbackComment('');
      setFeedbackModalOpen(true);
    }
  };

  const submitDownReview = async () => {
    if (!feedbackMessageId) return;
    try {
      setSubmittingReview(true);
      await fetch(`${API_BASE}/feedback`, {
        method: 'POST',
        headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
        body: JSON.stringify({ message_id: feedbackMessageId, rating: 'down', reason_tags: feedbackTags, comment: feedbackComment })
      });
      setSubmittedReviews(prev => ({ ...prev, [feedbackMessageId]: 'down' }));
      setFeedbackModalOpen(false);
    } catch(e) {} 
    finally { setSubmittingReview(false); }
  };

  const sendMessage = (customText = null) => {
    const textToSend = customText || inputText;
    if (!textToSend.trim() && !attachedImage) return;

    const userText = textToSend;
    const base64Img = attachedImage?.base64;
    const userImgUri = attachedImage?.uri;
    
    setInputText('');
    setAttachedImage(null);
    Keyboard.dismiss();

    const userMsgId = Date.now().toString();
    const botMsgId = (Date.now() + 1).toString();

    setMessages(prev => [
      ...prev, 
      { id: userMsgId, text: userText, imageUri: userImgUri, isUser: true },
      { id: botMsgId, text: '...', isUser: false, isStreaming: true }
    ]);

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${API_BASE}/chat`);
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    
    let seenBytes = 0;
    let buffer = '';
    let currentBotReply = "";
    
    xhr.onreadystatechange = () => {
      if (xhr.readyState === 3 || xhr.readyState === 4) {
        const newData = xhr.responseText.substring(seenBytes);
        seenBytes = xhr.responseText.length;
        buffer += newData;
        
        let boundary = buffer.indexOf('\n\n');
        while (boundary !== -1) {
          const chunk = buffer.substring(0, boundary);
          buffer = buffer.substring(boundary + 2);
          
          const lines = chunk.split('\n');
          let dataLines = [];
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              dataLines.push(line.substring(6));
            }
          }
          const dataStr = dataLines.join('\n');
          
          if (dataStr === '[DONE]') {
            setMessages(prev => prev.map(m => m.id === botMsgId ? { ...m, isStreaming: false } : m));
            if (isLoggedInGG && !activeConversationId) fetchConversations(token);
          } else if (dataStr) {
            if (dataStr.trim().startsWith('{')) {
              try {
                const parsed = JSON.parse(dataStr);
                if (typeof parsed === 'object' && parsed !== null) {
                  if (parsed.error) currentBotReply += `\n**[Lỗi: ${parsed.error}]**\n`;
                  if (parsed.conversation_id && !activeConversationId) setActiveConversationId(parsed.conversation_id);
                  setMessages(prev => prev.map(m => {
                    if (m.id === botMsgId) {
                      return {
                        ...m,
                        message_id: parsed.message_id || m.message_id,
                        step: parsed.step || m.step,
                        latency_ms: parsed.metrics ? parsed.metrics.total_latency_ms : (parsed.latency_ms || m.latency_ms),
                        sources: parsed.sources || m.sources
                      };
                    }
                    return m;
                  }));
                } else {
                  currentBotReply += dataStr;
                }
              } catch (err) {
                currentBotReply += dataStr; 
              }
            } else {
              currentBotReply += dataStr;
            }
          }
          boundary = buffer.indexOf('\n\n');
        }
        
        let cleanText = currentBotReply.replace(/:::card[\s\S]*?:::/g, '\n*[Dữ liệu thẻ thông tin ẩn trên Mobile]*\n');
        setMessages(prev => prev.map(m => m.id === botMsgId ? { ...m, text: cleanText || '...' } : m));
      }
      
      if (xhr.readyState === 4) {
        setMessages(prev => prev.map(m => m.id === botMsgId ? { ...m, isStreaming: false } : m));
      }
    };
    
    xhr.send(JSON.stringify({
      query: userText || "Phân tích hình ảnh này",
      image_base64: base64Img || null,
      deep_search: isDeepSearch,
      conversation_id: activeConversationId
    }));
  };

  const isDark = theme === 'dark';
  const bgColor = isDark ? '#020617' : '#F1F5F9';
  const cardColor = isDark ? '#0F172A' : '#FFFFFF';
  const textColor = isDark ? '#fff' : '#0F172A';
  const textMuted = isDark ? '#94A3B8' : '#334155';
  const borderColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.08)';
  const bgImage = isDark ? require('./assets/bg_dark.jpeg') : require('./assets/bg_light.jpeg');

  return (
    <ImageBackground source={bgImage} style={[styles.container, { backgroundColor: bgColor }]} imageStyle={{ width: Dimensions.get('window').width, height: Dimensions.get('window').height, resizeMode: 'cover' }}>
      <SafeAreaView style={{ flex: 1 }}>
        <StatusBar barStyle={isDark ? "light-content" : "dark-content"} backgroundColor="transparent" translucent />
        
        {/* HEADER */}
      <View style={[styles.header, { borderBottomColor: borderColor }]}>
        <TouchableOpacity style={[styles.iconButtonRound, { backgroundColor: cardColor, borderColor }]} onPress={toggleDrawer}>
          <Feather name="menu" size={20} color={textMuted} />
        </TouchableOpacity>
        <View style={styles.headerCenter}>
          <View style={styles.statusRow}>
            <View style={styles.statusDot} />
            <Text style={[styles.statusText, { color: textColor }]}>AI Online <MaterialCommunityIcons name="check-decagram" size={14} color="#00E6A8" /></Text>
          </View>
          <Text style={[styles.statusSubtitle, { color: textMuted }]}>{loadingToken ? "Đang kết nối..." : "Dữ liệu cập nhật 05/06/2026"}</Text>
        </View>
        <View style={styles.headerRight}>
          <TouchableOpacity style={[styles.iconButtonRound, { backgroundColor: cardColor, borderColor }]} onPress={() => setIsNotifOpen(true)}>
            <View style={styles.notificationBadge}><Text style={styles.badgeText}>2</Text></View>
            <Feather name="bell" size={20} color={textMuted} />
          </TouchableOpacity>
          {isLoggedInGG ? (
            <TouchableOpacity style={[styles.avatarButton, { backgroundColor: cardColor, borderColor }]} onPress={() => setIsUserModalOpen(true)}>
              {userInfo?.picture ? (
                <Image source={{ uri: userInfo.picture }} style={styles.avatarCircle} />
              ) : (
                <View style={styles.avatarCircle}><Text style={styles.avatarText}>{userInfo?.initial || 'L'}</Text></View>
              )}
              <Feather name="chevron-down" size={14} color={textMuted} />
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.loginHeaderBtn} onPress={handleGGLogin}>
              <MaterialCommunityIcons name="google" size={16} color="#DB4437" />
              <Text style={styles.loginHeaderText}>Đăng nhập</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* MAIN SCROLL VIEW */}
      <ScrollView 
        style={styles.mainContent} 
        contentContainerStyle={{ paddingBottom: 150 }}
        ref={scrollViewRef}
        onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
      >
        {messages.length === 0 ? (
          <>
            {/* HERO SECTION */}
            <View style={styles.heroSection}>
              <View style={styles.heroTextContainer}>
                <Text style={styles.brandSubtitle}>● XANH SM AI ASSISTANT</Text>
                <Text style={[styles.heroTitle, { color: textColor }]}>Xin chào {userInfo?.name?.split(' ')[0] || 'Dũng'} 👋</Text>
                <Text style={styles.heroTitleGreen}>Tôi có thể giúp gì cho bạn?</Text>
                <Text style={[styles.heroDesc, { color: isDark ? '#E2E8F0' : '#475569' }]}>Tôi có thể giúp bạn tìm hiểu dịch vụ, giá cước, xe điện, ưu đãi và chính sách của Xanh SM.</Text>
              </View>
              <Animated.Image source={require('./assets/bot.png')} style={[styles.botImage, { transform: [{ translateY: floatAnim }] }]} resizeMode="contain" />
            </View>

            {/* GRID CARDS */}
            <View style={styles.gridContainer}>
              <TouchableOpacity onPress={() => sendMessage("Giá cước dịch vụ Xanh SM như thế nào?")} style={[styles.card, { backgroundColor: cardColor, borderColor }]}>
                <MaterialCommunityIcons name="car-electric" size={24} color="#00E6A8" style={styles.cardIcon} />
                <Text style={[styles.cardTitle, { color: textColor }]}>Giá cước dịch vụ</Text>
                <Text style={[styles.cardDesc, { color: textMuted }]}>Xem bảng giá chi tiết cho từng loại dịch vụ</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => sendMessage("Tôi muốn thuê xe VinFast chạy dịch vụ")} style={[styles.card, { backgroundColor: cardColor, borderColor }]}>
                <Feather name="key" size={20} color="#3B82F6" style={styles.cardIcon} />
                <Text style={[styles.cardTitle, { color: textColor }]}>Thuê xe chạy dịch vụ</Text>
                <Text style={[styles.cardDesc, { color: textMuted }]}>Thông tin chi tiết về chính sách thuê xe điện</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => sendMessage("Có ưu đãi gì mới không?")} style={[styles.card, { backgroundColor: cardColor, borderColor }]}>
                <Feather name="tag" size={20} color="#F59E0B" style={styles.cardIcon} />
                <Text style={[styles.cardTitle, { color: textColor }]}>Ưu đãi & khuyến mãi</Text>
                <Text style={[styles.cardDesc, { color: textMuted }]}>Các chương trình ưu đãi mới nhất hiện nay</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => sendMessage("Cho tôi xem tin tức mới nhất của Xanh SM")} style={[styles.card, { backgroundColor: cardColor, borderColor }]}>
                <Feather name="file-text" size={20} color="#A855F7" style={styles.cardIcon} />
                <Text style={[styles.cardTitle, { color: textColor }]}>Tin tức Xanh SM</Text>
                <Text style={[styles.cardDesc, { color: textMuted }]}>Cập nhật tin tức, sự kiện và thông báo mới</Text>
              </TouchableOpacity>
            </View>
          </>
        ) : (
          /* CHAT MESSAGES */
          <View style={styles.chatContainer}>
            {messages.map((msg) => (
              <View key={msg.id} style={[styles.messageWrapper, msg.isUser ? styles.userWrapper : styles.botWrapper]}>
                
                <View style={[styles.messageBubble, msg.isUser ? styles.userBubble : [styles.botBubble, { backgroundColor: cardColor, borderColor }]]}>
                  {/* BOT STREAMING ANIMATION & TEXT */}
                  {!msg.isUser && msg.isStreaming && (!msg.text || msg.text === '...') && (
                    <View style={styles.botThinkingRow}>
                      <Animated.Image source={require('./assets/bot.png')} style={[styles.smallBotAvatar, { transform: [{ translateY: botAvatarFloatAnim }] }]} />
                      <Text style={styles.botThinkingText}>{msg.step ? msg.step : 'Đang suy nghĩ...'}</Text>
                    </View>
                  )}
                  {msg.imageUri && <Image source={{ uri: msg.imageUri }} style={styles.chatImage} resizeMode="cover" />}
                  {msg.text && msg.text !== '...' ? (
                    msg.isUser ? (
                      <Text style={[styles.messageText, styles.userText]}>{msg.text}</Text>
                    ) : (
                      <Markdown style={{
                        body: { color: isDark ? '#E2E8F0' : '#0F172A', fontSize: 15, lineHeight: 24 },
                        code_inline: { backgroundColor: isDark ? 'rgba(0, 230, 168, 0.1)' : 'rgba(0,200,151,0.1)', color: '#00E6A8', borderRadius: 4, padding: 2 },
                        strong: { fontWeight: 'bold', color: textColor },
                        heading1: { fontSize: 22, color: '#00E6A8', fontWeight: 'bold', marginVertical: 8 },
                        heading2: { fontSize: 18, color: '#00E6A8', fontWeight: 'bold', marginVertical: 8 },
                        heading3: { fontSize: 16, color: '#00E6A8', fontWeight: 'bold', marginVertical: 6 },
                        link: { color: '#3B82F6', textDecorationLine: 'underline' },
                        table: { borderWidth: 1, borderColor: isDark ? 'rgba(0, 230, 168, 0.2)' : 'rgba(0,0,0,0.1)', borderRadius: 8, marginVertical: 10, width: '100%' },
                        thead: { backgroundColor: isDark ? 'rgba(0, 230, 168, 0.1)' : '#f1f5f9' },
                        th: { padding: 8, borderBottomWidth: 1, borderBottomColor: isDark ? 'rgba(0, 230, 168, 0.2)' : 'rgba(0,0,0,0.1)', fontWeight: 'bold', color: '#00E6A8' },
                        tr: { borderBottomWidth: 1, borderBottomColor: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0,0,0,0.05)' },
                        td: { padding: 8, color: isDark ? '#E2E8F0' : '#0F172A' }
                      }}>{msg.text}</Markdown>
                    )
                  ) : null}
                </View>

                {/* Sources & Citations */}
                {!msg.isUser && msg.sources && msg.sources.length > 0 && (
                  <View style={styles.sourcesContainer}>
                    {msg.sources.slice(0, 3).map((src, i) => (
                      <TouchableOpacity key={i} style={styles.sourceTag} onPress={() => src.url && Linking.openURL(src.url)}>
                        <Feather name="link-2" size={10} color="#00E6A8" />
                        <Text style={styles.sourceText} numberOfLines={1} ellipsizeMode="tail">{src.source || 'Tài liệu'}</Text>
                      </TouchableOpacity>
                    ))}
                  </View>
                )}

                {/* Footer (Latency + Feedback) - Chỉ hiện khi ĐÃ STREAM XONG */}
                {!msg.isUser && !msg.isStreaming && (
                  <View style={[styles.messageFooter, { borderTopColor: borderColor }]}>
                    <View style={styles.latencyRow}>
                      <Text style={[styles.latencyText, { color: textMuted }]}>⏱️ {msg.latency_ms ? `Tổng thời gian: ${Math.round(msg.latency_ms)}ms` : 'Tổng thời gian: N/A'}</Text>
                    </View>
                    {msg.message_id && (
                      <View style={styles.feedbackRow}>
                        <TouchableOpacity onPress={() => handleReviewClick(msg.message_id, 'up')} disabled={!!submittedReviews[msg.message_id]} style={[styles.feedbackBtn, submittedReviews[msg.message_id] === 'up' && styles.feedbackBtnActive]}>
                          <Feather name="thumbs-up" size={14} color={submittedReviews[msg.message_id] === 'up' ? '#00E6A8' : textMuted} />
                        </TouchableOpacity>
                        <TouchableOpacity onPress={() => handleReviewClick(msg.message_id, 'down')} disabled={!!submittedReviews[msg.message_id]} style={[styles.feedbackBtn, submittedReviews[msg.message_id] === 'down' && styles.feedbackBtnActiveDown]}>
                          <Feather name="thumbs-down" size={14} color={submittedReviews[msg.message_id] === 'down' ? '#EF4444' : textMuted} />
                        </TouchableOpacity>
                      </View>
                    )}
                  </View>
                )}
              </View>
            ))}
          </View>
        )}
      </ScrollView>

      {/* INPUT BAR */}
      <KeyboardAvoidingView behavior={Platform.OS === "ios" ? "padding" : "height"} style={styles.absoluteInput}>
        <View style={[styles.inputContainer, { backgroundColor: cardColor, borderColor }]}>
          {attachedImage && (
            <View style={styles.previewContainer}>
              <Image source={{ uri: attachedImage.uri }} style={styles.previewImage} />
              <TouchableOpacity style={styles.removeImageBtn} onPress={() => setAttachedImage(null)}>
                <Ionicons name="close-circle" size={20} color="#EF4444" />
              </TouchableOpacity>
            </View>
          )}

          <TextInput 
            ref={textInputRef}
            style={[styles.input, { color: textColor }]} 
            placeholder="Hỏi Xanh SM bất cứ điều gì..." 
            placeholderTextColor={textMuted}
            value={inputText}
            onChangeText={setInputText}
            multiline
          />
          
          <View style={[styles.divider, { backgroundColor: borderColor }]} />

          <View style={styles.inputActionsRow}>
            <View style={styles.actionLeft}>
              <TouchableOpacity style={[styles.actionIconBtn, { backgroundColor: borderColor }]} onPress={pickImage}>
                <Ionicons name="image-outline" size={20} color={attachedImage ? "#00E6A8" : textMuted} />
              </TouchableOpacity>
              
              <TouchableOpacity onPress={() => setIsDeepSearch(!isDeepSearch)}>
                {isDeepSearch ? (
                  <LinearGradient colors={['rgba(99,102,241,0.2)', 'rgba(168,85,247,0.2)']} style={styles.deepSearchActive}>
                    <Ionicons name="search" size={14} color="#818CF8" />
                    <Text style={styles.deepSearchActiveText}>Deep Search</Text>
                  </LinearGradient>
                ) : (
                  <View style={styles.deepSearchBtn}>
                    <Ionicons name="search" size={14} color={textMuted} />
                  </View>
                )}
              </TouchableOpacity>
            </View>

            <View style={styles.actionRight}>
              <TouchableOpacity style={[styles.actionIconBtn, { backgroundColor: borderColor }]} onPress={() => Alert.alert("Thông báo", "Tính năng Voice-to-Text native trên Mobile đang được phát triển. Vui lòng sử dụng tính năng đọc chính tả trên bàn phím của bạn.")}>
                <Feather name="mic" size={20} color={textMuted} />
              </TouchableOpacity>
              <TouchableOpacity 
                style={[styles.sendBtn, (inputText || attachedImage) ? styles.sendBtnActive : { backgroundColor: borderColor }]}
                onPress={() => sendMessage()}
                disabled={!inputText.trim() && !attachedImage}
              >
                <Feather name="send" size={16} color={(inputText || attachedImage) ? "#fff" : textMuted} />
              </TouchableOpacity>
            </View>
          </View>
        </View>
      </KeyboardAvoidingView>

      {/* SIDEBAR (NAV DRAWER) */}
      {isDrawerOpen && (
        <TouchableWithoutFeedback onPress={toggleDrawer}>
          <View style={[StyleSheet.absoluteFill, { backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 100 }]} />
        </TouchableWithoutFeedback>
      )}
      <Animated.View style={[styles.drawerContainer, { transform: [{ translateX: drawerAnim }], backgroundColor: cardColor, borderRightColor: borderColor }]}>
        <View style={styles.drawerHeader}>
          <View style={{flexDirection:'row', alignItems:'center', gap:10}}>
            <ExpoImage source={require('./assets/logo.svg')} style={{width: 140, height: 40}} contentFit="contain" />
          </View>
          <TouchableOpacity onPress={toggleDrawer}><Feather name="x" size={24} color={textMuted} /></TouchableOpacity>
        </View>

        <TouchableOpacity style={styles.newChatBtn} onPress={startNewChat}>
          <LinearGradient colors={['#00c897', '#00a67d']} style={styles.newChatGrad} start={{x:0, y:0}} end={{x:1, y:0}}>
            <Feather name="plus" size={18} color="#fff" />
            <Text style={styles.newChatText}>Đoạn chat mới</Text>
          </LinearGradient>
        </TouchableOpacity>

        {isLoggedInGG && (
          <View style={{ flex: 1 }}>
            <Text style={styles.historyHeader}>Lịch sử trò chuyện</Text>
            <ScrollView showsVerticalScrollIndicator={false}>
              {conversations.length === 0 ? (
                <Text style={{color:textMuted, fontSize:12, fontStyle:'italic'}}>Chưa có lịch sử chat.</Text>
              ) : (
                conversations.map(conv => (
                  <TouchableOpacity key={conv.id} style={[styles.historyItem, activeConversationId === conv.id && styles.historyItemActive]} onPress={() => loadConversation(conv.id)}>
                    <Feather name="message-square" size={16} color={activeConversationId === conv.id ? "#00E6A8" : textMuted} />
                    <Text style={[styles.historyText, { color: activeConversationId === conv.id ? '#00E6A8' : textColor }]} numberOfLines={1}>{conv.title || 'New Conversation'}</Text>
                  </TouchableOpacity>
                ))
              )}
            </ScrollView>
          </View>
        )}

        <View style={[styles.drawerFooter, { borderTopColor: borderColor }]}>
          <View style={styles.themeToggleRow}>
            <Text style={[styles.historyText, { color: textColor }]}>Giao diện Tối (Dark Mode)</Text>
            <TouchableOpacity onPress={() => handleToggleTheme(!isDark)} style={[styles.switch, isDark ? styles.switchOn : styles.switchOff]}>
              <View style={[styles.switchThumb, isDark ? styles.switchThumbOn : styles.switchThumbOff]} />
            </TouchableOpacity>
          </View>

          {isLoggedInGG ? (
            <TouchableOpacity style={styles.logoutRow} onPress={handleLogout}>
              <Feather name="log-out" size={18} color="#EF4444" />
              <Text style={styles.logoutText}>Đăng xuất</Text>
            </TouchableOpacity>
          ) : (
            <TouchableOpacity style={styles.drawerLoginBtn} onPress={handleGGLogin} disabled={!request || ggLoading}>
              <MaterialCommunityIcons name="google" size={18} color="#DB4437" />
              <Text style={styles.drawerLoginText}>{ggLoading ? 'Đang tải...' : 'Đăng nhập Google'}</Text>
            </TouchableOpacity>
          )}
        </View>
      </Animated.View>

      {/* NOTIFICATION MODAL */}
      <Modal visible={isNotifOpen} transparent animationType="fade">
        <TouchableWithoutFeedback onPress={() => setIsNotifOpen(false)}>
          <View style={styles.overlayTransparentCenter}>
            <TouchableWithoutFeedback>
              <View style={[styles.notifModal, { backgroundColor: cardColor, borderColor }]}>
                <Text style={[styles.notifModalTitle, { color: textColor }]}>Thông báo hệ thống</Text>
                <View style={[styles.notifItem, { borderBottomColor: borderColor }]}>
                  <View style={[styles.notifDot, { backgroundColor: '#FFCA00' }]} />
                  <Text style={[styles.notifItemText, { color: textColor }]}>📸 Bổ sung tính năng thêm hình ảnh (Đọc lỗi xe tự động bằng NLU/Vision).</Text>
                </View>
                <View style={styles.notifItem}>
                  <View style={[styles.notifDot, { backgroundColor: '#00E6A8' }]} />
                  <Text style={[styles.notifItemText, { color: textColor }]}>🔍 Trải nghiệm tính năng Deep-Search: Nghiên cứu chuyên sâu tài liệu phức tạp.</Text>
                </View>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>

      {/* USER PROFILE MODAL */}
      <Modal visible={isUserModalOpen} transparent animationType="fade">
        <TouchableWithoutFeedback onPress={() => setIsUserModalOpen(false)}>
          <View style={styles.overlayTransparentCenter}>
            <TouchableWithoutFeedback>
              <View style={[styles.userModal, { backgroundColor: cardColor, borderColor }]}>
                <View style={styles.userModalHeader}>
                  <Text style={[styles.userModalTitle, { color: textColor }]}>Tài Khoản</Text>
                </View>
                {isLoggedInGG ? (
                  <View style={styles.userInfo}>
                    {userInfo?.picture ? (
                      <Image source={{ uri: userInfo.picture }} style={{width: 60, height: 60, borderRadius: 30}} />
                    ) : (
                      <Ionicons name="checkmark-circle" size={40} color="#00E6A8" />
                    )}
                    <Text style={[styles.userInfoName, { color: textColor }]}>{userInfo?.name || "Người dùng"}</Text>
                    <Text style={[styles.userInfoEmail, { color: textMuted }]}>{userInfo?.email || "Đã liên kết Google"}</Text>
                    <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout}>
                      <Text style={styles.logoutText}>Đăng xuất</Text>
                    </TouchableOpacity>
                  </View>
                ) : (
                  <View style={styles.loginContainer}>
                    <Text style={[styles.loginDesc, { color: textMuted }]}>Đăng nhập để lưu lịch sử chat và nhận ưu đãi riêng.</Text>
                    <TouchableOpacity style={styles.ggBtn} onPress={handleGGLogin} disabled={!request || ggLoading}>
                      <MaterialCommunityIcons name="google" size={20} color="#DB4437" />
                      <Text style={styles.ggBtnText}>{ggLoading ? "Đang kết nối..." : "Đăng nhập bằng Google"}</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>

      {/* FEEDBACK MODAL */}
      <Modal visible={feedbackModalOpen} transparent animationType="fade">
        <TouchableWithoutFeedback onPress={() => setFeedbackModalOpen(false)}>
          <View style={styles.overlayTransparentCenter}>
            <TouchableWithoutFeedback>
              <View style={[styles.userModal, { backgroundColor: cardColor, borderColor }]}>
                <Text style={[styles.notifModalTitle, { color: textColor, marginBottom: 10 }]}>Báo cáo câu trả lời</Text>
                <Text style={{color: textMuted, fontSize: 13, marginBottom: 15}}>Tại sao bạn không hài lòng với câu trả lời này?</Text>
                
                <View style={{flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 15}}>
                  {['Sai sự thật', 'Thiếu thông tin', 'Không liên quan', 'Lỗi hiển thị'].map(tag => (
                    <TouchableOpacity 
                      key={tag} 
                      onPress={() => setFeedbackTags(prev => prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag])}
                      style={[styles.sourceTag, feedbackTags.includes(tag) && { backgroundColor: 'rgba(239,68,68,0.1)', borderColor: '#EF4444' }]}
                    >
                      <Text style={[styles.sourceText, { color: feedbackTags.includes(tag) ? '#EF4444' : textMuted }]}>{tag}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <TextInput 
                  style={[styles.inputContainer, { color: textColor, minHeight: 80, borderColor, marginBottom: 15 }]} 
                  placeholder="Thêm ý kiến của bạn..." 
                  placeholderTextColor={textMuted}
                  value={feedbackComment}
                  onChangeText={setFeedbackComment}
                  multiline
                />

                <TouchableOpacity 
                  style={[styles.ggBtn, { backgroundColor: '#EF4444', justifyContent: 'center' }]} 
                  onPress={submitDownReview}
                  disabled={submittingReview}
                >
                  <Text style={{color: '#fff', fontWeight: 'bold'}}>{submittingReview ? 'Đang gửi...' : 'Gửi góp ý'}</Text>
                </TouchableOpacity>
              </View>
            </TouchableWithoutFeedback>
          </View>
        </TouchableWithoutFeedback>
      </Modal>

    </SafeAreaView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 15, paddingVertical: 10, borderBottomWidth: 1 },
  iconButtonRound: { width: 40, height: 40, borderRadius: 20, justifyContent: 'center', alignItems: 'center', borderWidth: 1 },
  headerCenter: { alignItems: 'center' },
  statusRow: { flexDirection: 'row', alignItems: 'center', gap: 5 },
  statusDot: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#00E6A8', shadowColor: '#00E6A8', shadowOpacity: 1, shadowRadius: 5 },
  statusText: { fontSize: 16, fontWeight: '700' },
  statusSubtitle: { fontSize: 10, marginTop: 2, fontStyle: 'italic' },
  headerRight: { flexDirection: 'row', gap: 10, alignItems: 'center' },
  notificationBadge: { position: 'absolute', top: 5, right: 8, backgroundColor: '#EF4444', width: 14, height: 14, borderRadius: 7, justifyContent: 'center', alignItems: 'center', zIndex: 10 },
  badgeText: { color: '#fff', fontSize: 8, fontWeight: 'bold' },
  avatarButton: { flexDirection: 'row', alignItems: 'center', gap: 5, padding: 5, paddingRight: 10, borderRadius: 20, borderWidth: 1 },
  avatarCircle: { width: 28, height: 28, borderRadius: 14, backgroundColor: '#00E6A8', justifyContent: 'center', alignItems: 'center', overflow: 'hidden' },
  avatarText: { color: '#020617', fontWeight: 'bold', fontSize: 12 },
  loginHeaderBtn: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: '#fff', paddingHorizontal: 12, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: '#E2E8F0' },
  loginHeaderText: { fontSize: 12, fontWeight: 'bold', color: '#020617' },
  
  mainContent: { flex: 1, paddingHorizontal: 15, paddingTop: 20 },
  heroSection: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 30 },
  heroTextContainer: { flex: 1, paddingRight: 10 },
  brandSubtitle: { color: '#00E6A8', fontSize: 10, fontWeight: 'bold', letterSpacing: 1, marginBottom: 5 },
  heroTitle: { fontSize: 26, fontWeight: '900', marginBottom: 2 },
  heroTitleGreen: { color: '#00E6A8', fontSize: 24, fontWeight: '900', marginBottom: 10 },
  heroDesc: { fontSize: 13, lineHeight: 20 },
  botImage: { width: 100, height: 120 },

  gridContainer: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between', gap: 10 },
  card: { width: '48%', padding: 15, borderRadius: 20, borderWidth: 1, marginBottom: 5 },
  cardIcon: { marginBottom: 10 },
  cardTitle: { fontSize: 14, fontWeight: 'bold', marginBottom: 5 },
  cardDesc: { fontSize: 11, lineHeight: 16 },

  chatContainer: { gap: 15, paddingBottom: 20 },
  messageWrapper: { maxWidth: '90%' },
  userWrapper: { alignSelf: 'flex-end' },
  botWrapper: { alignSelf: 'flex-start' },
  botThinkingRow: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 8, marginLeft: 5 },
  smallBotAvatar: { width: 24, height: 24 },
  botThinkingText: { color: '#00E6A8', fontSize: 13, fontStyle: 'italic', fontWeight: 'bold' },
  messageBubble: { padding: 15, borderRadius: 20 },
  userBubble: { backgroundColor: '#00A651', borderBottomRightRadius: 5 },
  botBubble: { borderBottomLeftRadius: 5, borderWidth: 1, borderColor: 'rgba(0, 230, 168, 0.1)' },
  messageText: { fontSize: 16, lineHeight: 24 },
  userText: { color: '#fff' },
  chatImage: { width: 200, height: 200, borderRadius: 10, marginBottom: 8 },

  sourcesContainer: { flexDirection: 'row', flexWrap: 'wrap', gap: 6, marginTop: 8 },
  sourceTag: { flexDirection: 'row', alignItems: 'center', gap: 4, backgroundColor: 'rgba(0,230,168,0.1)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(0,230,168,0.2)' },
  sourceText: { color: '#00E6A8', fontSize: 10, fontWeight: 'bold', maxWidth: 100 },

  messageFooter: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: 10, borderTopWidth: 1, paddingTop: 8 },
  latencyRow: { flexDirection: 'row', alignItems: 'center' },
  latencyText: { fontSize: 10, fontWeight: 'bold' },
  feedbackRow: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  feedbackBtn: { padding: 4, borderRadius: 6 },
  feedbackBtnActive: { backgroundColor: 'rgba(0,230,168,0.1)' },
  feedbackBtnActiveDown: { backgroundColor: 'rgba(239,68,68,0.1)' },

  absoluteInput: { position: 'absolute', bottom: Platform.OS === 'ios' ? 25 : 15, left: 15, right: 15 },
  inputContainer: { borderRadius: 24, padding: 15, overflow: 'hidden', borderWidth: 1 },
  input: { fontSize: 15, minHeight: 40, maxHeight: 100, paddingBottom: 10 },
  previewContainer: { marginBottom: 10, flexDirection: 'row' },
  previewImage: { width: 60, height: 60, borderRadius: 8, borderWidth: 1, borderColor: '#00E6A8' },
  removeImageBtn: { position: 'absolute', top: -5, left: 50, borderRadius: 10 },
  divider: { height: 1, marginBottom: 10 },
  inputActionsRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  actionLeft: { flexDirection: 'row', alignItems: 'center', gap: 8, flex: 1 },
  actionIconBtn: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  deepSearchBtn: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12 },
  deepSearchActive: { flexDirection: 'row', alignItems: 'center', gap: 4, paddingHorizontal: 10, paddingVertical: 6, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(99,102,241,0.3)' },
  deepSearchActiveText: { color: '#818CF8', fontSize: 11, fontWeight: 'bold' },
  actionRight: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  sendBtn: { width: 32, height: 32, borderRadius: 16, justifyContent: 'center', alignItems: 'center' },
  sendBtnActive: { backgroundColor: '#00E6A8' },

  drawerContainer: { position: 'absolute', top: 0, bottom: 0, left: 0, width: 300, zIndex: 101, padding: 20, paddingTop: 50, borderRightWidth: 1 },
  drawerHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 },
  drawerTitle: { fontSize: 20, fontWeight: '900' },
  newChatBtn: { marginBottom: 25 },
  newChatGrad: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, paddingVertical: 14, borderRadius: 30, shadowColor: '#00E6A8', shadowOffset: {width:0,height:4}, shadowOpacity: 0.3, shadowRadius: 10 },
  newChatText: { color: '#fff', fontWeight: 'bold', fontSize: 15 },
  historyHeader: { fontSize: 14, fontWeight: 'bold', color: '#94A3B8', marginBottom: 15 },
  historyItem: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingVertical: 12, paddingHorizontal: 10, borderRadius: 12, marginBottom: 5 },
  historyItemActive: { backgroundColor: 'rgba(0,230,168,0.1)', borderColor: '#00E6A8', borderWidth: 1 },
  historyText: { fontSize: 14, flex: 1 },
  
  drawerFooter: { marginTop: 'auto', paddingTop: 20, borderTopWidth: 1, gap: 15, paddingBottom: 10 },
  themeToggleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 5 },
  switch: { width: 40, height: 22, borderRadius: 11, justifyContent: 'center', padding: 2 },
  switchOn: { backgroundColor: '#00E6A8' },
  switchOff: { backgroundColor: '#94A3B8' },
  switchThumb: { width: 18, height: 18, borderRadius: 9, backgroundColor: '#fff', shadowColor:'#000', shadowOpacity:0.2, shadowRadius:2 },
  switchThumbRight: { alignSelf: 'flex-end' },
  switchThumbLeft: { alignSelf: 'flex-start' },
  logoutRow: { flexDirection: 'row', alignItems: 'center', gap: 12, backgroundColor: 'rgba(239, 68, 68, 0.1)', paddingVertical: 12, paddingHorizontal: 15, borderRadius: 12 },
  logoutText: { color: '#EF4444', fontWeight: 'bold', fontSize: 14 },
  drawerLoginBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 10, backgroundColor: '#fff', paddingVertical: 12, borderRadius: 12 },
  drawerLoginText: { color: '#020617', fontWeight: 'bold', fontSize: 14 },

  overlayTransparentCenter: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(0,0,0,0.5)' },
  userModal: { width: '80%', borderRadius: 24, padding: 20, borderWidth: 1 },
  userModalHeader: { alignItems: 'center', marginBottom: 20 },
  userModalTitle: { fontSize: 18, fontWeight: 'bold' },
  loginContainer: { alignItems: 'center' },
  loginDesc: { fontSize: 13, textAlign: 'center', marginBottom: 20 },
  ggBtn: { flexDirection: 'row', alignItems: 'center', gap: 10, backgroundColor: '#fff', paddingHorizontal: 20, paddingVertical: 12, borderRadius: 24 },
  ggBtnText: { color: '#020617', fontWeight: 'bold', fontSize: 14 },
  userInfo: { alignItems: 'center', gap: 10 },
  userInfoName: { fontSize: 20, fontWeight: 'bold' },
  userInfoEmail: { fontSize: 14 },
  logoutBtn: { marginTop: 15, backgroundColor: 'rgba(239, 68, 68, 0.1)', paddingHorizontal: 20, paddingVertical: 10, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(239, 68, 68, 0.3)' },
  
  notifModal: { width: '85%', borderRadius: 20, padding: 20, borderWidth: 1, elevation: 5 },
  notifModalTitle: { fontSize: 18, fontWeight: 'bold', marginBottom: 15 },
  notifItem: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 12, backgroundColor: 'rgba(0, 230, 168, 0.05)', padding: 12, borderRadius: 12 },
  notifDot: { width: 8, height: 8, borderRadius: 4, backgroundColor: '#00E6A8' },
  notifItemText: { fontSize: 14, flex: 1 }
});
