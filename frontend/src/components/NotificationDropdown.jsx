import { createPortal } from 'react-dom';
import { Check, Mic, BookOpen, Lightbulb } from 'lucide-react';

const NotificationDropdown = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const content = (
    <div className="notification-portal-wrapper font-sans">
      {/* Backdrop */}
      <div 
        style={{
          position: 'fixed',
          inset: 0,
          zIndex: 999998,
          backgroundColor: 'rgba(0, 0, 0, 0.6)',
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)'
        }}
        onClick={onClose}
      />
      
      {/* Dropdown Content - Centered with fixed constraints */}
      <div 
        className="bg-surface dark:bg-[#0c1618] text-on-surface"
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '90%',
          maxWidth: '580px', // Adjusted to be more reasonable
          maxHeight: '85vh',
          zIndex: 999999, // Maximum priority
          borderRadius: '32px',
          boxShadow: '0 25px 60px -12px rgba(0, 0, 0, 0.7)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
          border: '1px solid rgba(128, 128, 128, 0.2)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div 
          className="border-b border-outline/10 bg-surface-container-low dark:bg-white/5"
          style={{
            padding: '24px 32px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            flexShrink: 0
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 900, display: 'flex', alignItems: 'center', gap: '10px' }}>
              Thông báo
              <span style={{ 
                padding: '2px 8px', 
                backgroundColor: '#ef4444', 
                borderRadius: '99px', 
                fontSize: '11px', 
                fontWeight: 900, 
                color: 'white'
              }}>2</span>
            </h3>
          </div>
          <button 
            className="text-primary hover:underline"
            style={{ fontSize: '12px', fontWeight: 700, background: 'none', border: 'none', cursor: 'pointer' }}
          >
            Đánh dấu đã đọc
          </button>
        </div>

        {/* Content */}
        <div 
          className="no-scrollbar"
          style={{
            padding: '32px',
            overflowY: 'auto',
            flexGrow: 1,
            backgroundColor: 'transparent'
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '28px' }}>
            {/* Notification Item */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
                <span style={{ padding: '3px 10px', backgroundColor: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6', fontSize: '10px', fontWeight: 900, borderRadius: '6px', flexShrink: 0, marginTop: '2px' }}>MỚI</span>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <h4 style={{ margin: 0, fontSize: '15px', fontWeight: 900, lineHeight: 1.4 }}>
                    🚀 Cập nhật Voice & Mở rộng kho tri thức Xanh SM
                  </h4>
                </div>
              </div>

              <div className="text-on-surface-variant" style={{ fontSize: '13px', lineHeight: 1.7, fontWeight: 500 }}>
                <p style={{ margin: '0 0 20px 0' }}>Chúng tôi vừa nâng cấp hệ thống AI nhằm mang đến trải nghiệm hỗ trợ nhanh chóng và chính xác hơn:</p>
                
                <div style={{ marginBottom: '20px' }}>
                  <div className="text-primary dark:text-[#00c897]" style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 900, marginBottom: '10px' }}>
                    <Mic size={16} />
                    <span>Bỏ sung tính năng Voice Chat</span>
                  </div>
                </div>

                <div style={{ marginBottom: '20px' }}>
                  <div className="text-primary dark:text-[#00c897]" style={{ display: 'flex', alignItems: 'center', gap: '10px', fontWeight: 900, marginBottom: '10px' }}>
                    <BookOpen size={16} />
                    <span>Mở rộng kho tri thức Xanh SM</span>
                  </div>
                  <p style={{ margin: '0 0 10px 0' }}>AI hiện có thể hỗ trợ nhiều nội dung hơn về:</p>
                  <ul style={{ margin: 0, paddingLeft: '24px', listStyleType: 'disc' }}>
                    <li>Chính sách và quy định dịch vụ</li>
                    <li>Hướng dẫn sử dụng ứng dụng</li>
                    <li>Hỗ trợ tài khoản và thanh toán</li>
                    <li>Các dòng xe và dịch vụ Xanh SM</li>
                    <li>Bảng giá, ưu đãi và khuyến mãi</li>
                    <li>Tin tức và cập nhật mới nhất từ Xanh SM</li>
                  </ul>
                </div>

                <div className="bg-amber-500/10 dark:bg-amber-500/5" style={{ padding: '16px', borderRadius: '20px', border: '1px solid rgba(245, 158, 11, 0.3)', display: 'flex', gap: '14px' }}>
                  <Lightbulb size={18} style={{ color: '#f59e0b', flexShrink: 0 }} />
                  <p style={{ margin: 0, fontStyle: 'italic', fontWeight: 700 }}>
                    Hãy thử đặt câu hỏi bằng văn bản hoặc giọng nói để trải nghiệm các tính năng mới.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Button */}
            <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '12px' }}>
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  onClose();
                }}
                style={{
                  width: '100%',
                  maxWidth: '240px',
                  padding: '14px 0',
                  borderRadius: '9999px',
                  backgroundColor: '#00c897',
                  color: 'white',
                  fontWeight: 900,
                  fontSize: '14px',
                  border: 'none',
                  cursor: 'pointer',
                  boxShadow: '0 8px 25px rgba(0, 200, 151, 0.4)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '10px',
                  transition: 'all 0.2s ease'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#00b084';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                  e.currentTarget.style.boxShadow = '0 10px 30px rgba(0, 200, 151, 0.5)';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = '#00c897';
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = '0 8px 25px rgba(0, 200, 151, 0.4)';
                }}
              >
                <Check size={18} />
                Đã hiểu
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );

  return createPortal(content, document.body);
};

export default NotificationDropdown;
