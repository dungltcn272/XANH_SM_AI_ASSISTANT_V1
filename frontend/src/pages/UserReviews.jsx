import { useState, useEffect, useCallback } from 'react';
import { api } from '../api';
import { RefreshCw, Search, ThumbsUp, ThumbsDown, CheckCircle, XCircle, AlertCircle, Eye, ArrowLeft, Send } from 'lucide-react';

const StatusBadge = ({ status }) => {
  switch (status) {
    case 'new': return <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full border border-blue-200">Mới</span>;
    case 'reviewed': return <span className="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full border border-gray-200">Đã xem</span>;
    case 'promoted': return <span className="px-2 py-1 bg-[#00c897]/10 text-[#00c897] text-xs rounded-full border border-[#00c897]/20 flex items-center gap-1"><CheckCircle size={12} /> Promoted</span>;
    case 'rejected': return <span className="px-2 py-1 bg-red-100 text-red-800 text-xs rounded-full border border-red-200 flex items-center gap-1"><XCircle size={12} /> Bỏ qua</span>;
    default: return <span>{status}</span>;
  }
};

export default function UserReviews() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  
  // Filters
  const [statusFilter, setStatusFilter] = useState('');
  const [ratingFilter, setRatingFilter] = useState('');
  const [keyword, setKeyword] = useState('');
  const [page, setPage] = useState(0);
  const limit = 20;

  // Selected Review
  const [selectedReview, setSelectedReview] = useState(null);
  const [reviewDetail, setReviewDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [adminNote, setAdminNote] = useState('');
  
  const fetchReviews = useCallback(async () => {
    setLoading(true);
    try {
      const filters = {
        limit,
        offset: page * limit,
        status: statusFilter,
        rating: ratingFilter,
        keyword
      };
      const data = await api.getAdminReviews(filters);
      setReviews(data.data);
      setTotal(data.total);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [limit, page, statusFilter, ratingFilter, keyword]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchReviews();
  }, [fetchReviews]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(0);
    fetchReviews();
  };

  const handleViewDetail = async (id) => {
    setSelectedReview(id);
    setDetailLoading(true);
    try {
      const data = await api.getAdminReviewDetail(id);
      setReviewDetail(data);
      setAdminNote(data.admin_note || '');
    } catch (e) {
      console.error(e);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleUpdateStatus = async (status) => {
    if (!reviewDetail) return;
    try {
      await api.updateAdminReviewStatus(reviewDetail.id, {
        status,
        admin_note: adminNote
      });
      // Update local state
      setReviewDetail(prev => ({ ...prev, status, admin_note: adminNote }));
      // Refresh list
      fetchReviews();
    } catch (e) {
      console.error("Failed to update status", e);
      alert("Cập nhật thất bại");
    }
  };

  if (selectedReview) {
    return (
      <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button 
              onClick={() => { setSelectedReview(null); setReviewDetail(null); }}
              className="p-2 bg-white/50 border border-outline-variant/20 rounded-xl hover:bg-white transition-all text-on-surface-variant"
            >
              <ArrowLeft size={20} />
            </button>
            <h1 className="text-2xl font-bold text-on-surface">Chi tiết Đánh giá</h1>
          </div>
          {reviewDetail && (
            <div className="flex items-center gap-3">
              <StatusBadge status={reviewDetail.status} />
              <div className="flex bg-white/50 border border-outline-variant/20 rounded-xl overflow-hidden p-1 gap-1">
                <button onClick={() => handleUpdateStatus('reviewed')} className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${reviewDetail.status === 'reviewed' ? 'bg-gray-200 text-gray-800' : 'hover:bg-gray-100'}`}>Reviewed</button>
                <button onClick={() => handleUpdateStatus('promoted')} className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${reviewDetail.status === 'promoted' ? 'bg-[#00c897] text-white' : 'hover:bg-[#00c897]/10 text-[#00c897]'}`}>Promote to Eval</button>
                <button onClick={() => handleUpdateStatus('rejected')} className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-all ${reviewDetail.status === 'rejected' ? 'bg-red-500 text-white' : 'hover:bg-red-50 text-red-600'}`}>Reject</button>
              </div>
            </div>
          )}
        </div>

        {detailLoading || !reviewDetail ? (
          <div className="flex justify-center items-center h-64">
            <RefreshCw className="animate-spin text-[#00c897]" size={32} />
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-6">
              {/* Query & Answer */}
              <div className="glass-panel p-6 rounded-2xl border border-outline-variant/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4">
                  {reviewDetail.rating === 'up' ? (
                    <div className="flex items-center gap-2 text-[#00c897] bg-[#00c897]/10 px-3 py-1 rounded-full font-bold">
                      <ThumbsUp size={16} /> Hữu ích
                    </div>
                  ) : (
                    <div className="flex items-center gap-2 text-red-500 bg-red-50 px-3 py-1 rounded-full font-bold">
                      <ThumbsDown size={16} /> Không hữu ích
                    </div>
                  )}
                </div>
                
                <h3 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Lượt Chat</h3>
                <div className="space-y-4">
                  <div className="bg-surface-container/50 p-4 rounded-xl border border-outline-variant/20">
                    <div className="text-xs font-semibold text-primary mb-1">USER</div>
                    <div className="text-on-surface text-sm">{reviewDetail.query || <em>Không xác định</em>}</div>
                  </div>
                  <div className="bg-white/50 p-4 rounded-xl border border-outline-variant/20">
                    <div className="text-xs font-semibold text-secondary mb-1">XANH SM BOT</div>
                    <div className="text-on-surface text-sm whitespace-pre-wrap">{reviewDetail.answer || <em>Không xác định</em>}</div>
                  </div>
                </div>
              </div>

              {/* Pipeline Trace */}
              <div className="glass-panel p-6 rounded-2xl border border-outline-variant/20">
                <h3 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4 flex items-center gap-2">
                  <AlertCircle size={16} /> Thông số Pipeline (Trace)
                </h3>
                {reviewDetail.pipeline_trace ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-white/50 p-3 rounded-xl border border-outline-variant/10 text-center">
                      <div className="text-xs text-on-surface-variant mb-1">Search</div>
                      <div className="font-bold text-primary">{reviewDetail.pipeline_trace.search_latency_ms || 0} ms</div>
                    </div>
                    <div className="bg-white/50 p-3 rounded-xl border border-outline-variant/10 text-center">
                      <div className="text-xs text-on-surface-variant mb-1">Rerank</div>
                      <div className="font-bold text-primary">{reviewDetail.pipeline_trace.rerank_latency_ms || 0} ms</div>
                    </div>
                    <div className="bg-white/50 p-3 rounded-xl border border-outline-variant/10 text-center">
                      <div className="text-xs text-on-surface-variant mb-1">Generation</div>
                      <div className="font-bold text-primary">{reviewDetail.pipeline_trace.generation_latency_ms || 0} ms</div>
                    </div>
                    <div className="bg-white/50 p-3 rounded-xl border border-outline-variant/10 text-center">
                      <div className="text-xs text-on-surface-variant mb-1">Tokens</div>
                      <div className="font-bold text-primary">{reviewDetail.pipeline_trace.total_tokens || 0}</div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-on-surface-variant italic">Không có dữ liệu trace cho tin nhắn này.</p>
                )}
                
                {reviewDetail.pipeline_trace && (
                  <div className="bg-[#1e1e1e] rounded-xl p-4 overflow-x-auto text-xs text-green-400 font-mono">
                    <pre>{JSON.stringify(reviewDetail.pipeline_trace, null, 2)}</pre>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-6">
              {/* User Feedback Info */}
              <div className="glass-panel p-6 rounded-2xl border border-outline-variant/20">
                <h3 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Chi tiết phản hồi</h3>
                
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-on-surface-variant mb-2">Lý do (Tags):</div>
                    <div className="flex flex-wrap gap-2">
                      {reviewDetail.reason_tags && reviewDetail.reason_tags.length > 0 ? (
                        reviewDetail.reason_tags.map((tag, idx) => (
                          <span key={idx} className="bg-red-50 text-red-600 border border-red-200 px-2 py-1 rounded-md text-xs font-medium">
                            {tag}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-on-surface-variant/50 italic">Không có</span>
                      )}
                    </div>
                  </div>
                  
                  <div>
                    <div className="text-xs text-on-surface-variant mb-2">Bình luận chi tiết:</div>
                    <div className="bg-white/50 p-3 rounded-xl border border-outline-variant/20 text-sm text-on-surface">
                      {reviewDetail.comment || <em className="text-on-surface-variant/50">Không có bình luận</em>}
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-outline-variant/20">
                    <div className="text-xs text-on-surface-variant">Ngày đánh giá:</div>
                    <div className="text-sm font-medium">{new Date(reviewDetail.created_at).toLocaleString('vi-VN')}</div>
                  </div>
                </div>
              </div>

              {/* Admin Note */}
              <div className="glass-panel p-6 rounded-2xl border border-outline-variant/20">
                <h3 className="text-sm font-bold text-on-surface-variant uppercase tracking-wider mb-4">Ghi chú quản trị</h3>
                <textarea
                  value={adminNote}
                  onChange={(e) => setAdminNote(e.target.value)}
                  placeholder="Nhập ghi chú hoặc phân tích lỗi..."
                  className="w-full h-32 bg-white/50 border border-outline-variant/20 rounded-xl p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary mb-3"
                ></textarea>
                <button 
                  onClick={() => handleUpdateStatus(reviewDetail.status)}
                  className="w-full flex justify-center items-center gap-2 py-2 bg-gradient-to-r from-primary to-secondary text-white font-bold rounded-xl hover:opacity-90 transition-opacity"
                >
                  <Send size={16} /> Lưu ghi chú
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-on-surface mb-1">User Reviews & Feedback</h1>
          <p className="text-on-surface-variant text-sm">Quản lý phản hồi của người dùng để cải thiện chất lượng AI</p>
        </div>
        
        <button onClick={fetchReviews} className="flex items-center gap-2 px-4 py-2 bg-white/50 border border-outline-variant/20 rounded-xl hover:bg-white transition-all text-on-surface-variant font-medium text-sm">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          Làm mới
        </button>
      </div>

      <div className="glass-panel p-4 rounded-2xl border border-outline-variant/20 flex flex-col md:flex-row gap-4">
        <form onSubmit={handleSearch} className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant" size={18} />
          <input 
            type="text" 
            placeholder="Tìm kiếm nội dung câu hỏi, trả lời, comment..."
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            className="w-full pl-10 pr-4 py-2.5 bg-white/50 border border-outline-variant/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:bg-white transition-all text-sm"
          />
        </form>
        
        <div className="flex gap-2">
          <select 
            value={ratingFilter} 
            onChange={(e) => setRatingFilter(e.target.value)}
            className="px-4 py-2.5 bg-white/50 border border-outline-variant/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm min-w-[140px]"
          >
            <option value="">Tất cả Rating</option>
            <option value="up">👍 Hữu ích</option>
            <option value="down">👎 Không hữu ích</option>
          </select>
          
          <select 
            value={statusFilter} 
            onChange={(e) => setStatusFilter(e.target.value)}
            className="px-4 py-2.5 bg-white/50 border border-outline-variant/20 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary text-sm min-w-[140px]"
          >
            <option value="">Tất cả Trạng thái</option>
            <option value="new">Mới</option>
            <option value="reviewed">Đã xem</option>
            <option value="promoted">Promoted</option>
            <option value="rejected">Bỏ qua</option>
          </select>
        </div>
      </div>

      <div className="glass-panel rounded-2xl border border-outline-variant/20 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-surface-container/50 text-on-surface-variant font-semibold border-b border-outline-variant/20">
              <tr>
                <th className="p-4 w-12">Rating</th>
                <th className="p-4 min-w-[250px]">Câu hỏi & Lý do</th>
                <th className="p-4">Trạng thái</th>
                <th className="p-4">Ngày tạo</th>
                <th className="p-4 w-16"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-variant/10">
              {loading && reviews.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-on-surface-variant">
                    <RefreshCw className="animate-spin inline-block mr-2" size={20} /> Đang tải...
                  </td>
                </tr>
              ) : reviews.length === 0 ? (
                <tr>
                  <td colSpan="5" className="p-8 text-center text-on-surface-variant">
                    Không có phản hồi nào
                  </td>
                </tr>
              ) : (
                reviews.map(review => (
                  <tr key={review.id} className="hover:bg-white/30 transition-colors">
                    <td className="p-4">
                      {review.rating === 'up' ? (
                        <div className="w-8 h-8 rounded-full bg-[#00c897]/10 text-[#00c897] flex items-center justify-center">
                          <ThumbsUp size={16} />
                        </div>
                      ) : (
                        <div className="w-8 h-8 rounded-full bg-red-100 text-red-500 flex items-center justify-center">
                          <ThumbsDown size={16} />
                        </div>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="font-medium text-on-surface line-clamp-1">{review.query}</div>
                      {review.reason_tags && review.reason_tags.length > 0 && (
                        <div className="flex gap-1 mt-1">
                          {review.reason_tags.map((tag, idx) => (
                            <span key={idx} className="text-[10px] px-1.5 py-0.5 rounded border border-outline-variant/30 text-on-surface-variant bg-white/50">{tag}</span>
                          ))}
                        </div>
                      )}
                      {review.comment && (
                        <div className="text-xs text-on-surface-variant/70 mt-1 line-clamp-1 italic">"{review.comment}"</div>
                      )}
                    </td>
                    <td className="p-4">
                      <StatusBadge status={review.status} />
                    </td>
                    <td className="p-4 text-on-surface-variant text-xs">
                      {new Date(review.created_at).toLocaleString('vi-VN')}
                    </td>
                    <td className="p-4 text-right">
                      <button 
                        onClick={() => handleViewDetail(review.id)}
                        className="p-2 text-[#00c897] hover:bg-[#00c897]/10 rounded-lg transition-colors"
                      >
                        <Eye size={18} />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
        
        <div className="p-4 border-t border-outline-variant/20 flex items-center justify-between bg-white/30">
          <div className="text-sm text-on-surface-variant">
            Hiển thị <span className="font-medium text-on-surface">{reviews.length}</span> / <span className="font-medium text-on-surface">{total}</span>
          </div>
          <div className="flex gap-2">
            <button 
              disabled={page === 0} 
              onClick={() => setPage(p => p - 1)}
              className="px-3 py-1.5 text-sm bg-white border border-outline-variant/20 rounded-lg disabled:opacity-50"
            >
              Trước
            </button>
            <button 
              disabled={(page + 1) * limit >= total} 
              onClick={() => setPage(p => p + 1)}
              className="px-3 py-1.5 text-sm bg-white border border-outline-variant/20 rounded-lg disabled:opacity-50"
            >
              Sau
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
