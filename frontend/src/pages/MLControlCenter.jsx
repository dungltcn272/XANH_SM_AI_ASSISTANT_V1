import { useCallback, useEffect, useState } from 'react';
import { Activity, Bot, Database, RefreshCw } from 'lucide-react';
import { api, API_BASE } from '../api';

const MLControlCenter = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [training, setTraining] = useState(false);
  const [message, setMessage] = useState('');

  const fetchStatus = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api._fetch(`${API_BASE}/admin/ml/status`);
      if (!res.ok) throw new Error('Failed to fetch status');
      setStatus(await res.json());
    } catch (err) {
      console.error(err);
      setMessage('Không thể tải trạng thái ML.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    const loadInitialStatus = async () => {
      try {
        const res = await api._fetch(`${API_BASE}/admin/ml/status`);
        if (!res.ok) throw new Error('Failed to fetch status');
        const data = await res.json();
        if (!cancelled) setStatus(data);
      } catch (err) {
        console.error(err);
        if (!cancelled) setMessage('Không thể tải trạng thái ML.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    void loadInitialStatus();
    return () => {
      cancelled = true;
    };
  }, []);

  const handleTrain = async () => {
    if (!window.confirm('Bạn có chắc muốn kích hoạt quá trình huấn luyện? Việc này có thể mất vài phút.')) return;

    setTraining(true);
    setMessage('');
    try {
      const res = await api._fetch(`${API_BASE}/admin/ml/train`, { method: 'POST' });
      const data = await res.json();
      setMessage(data.message || 'Đã bắt đầu quá trình huấn luyện.');
    } catch (err) {
      console.error(err);
      setMessage('Có lỗi xảy ra khi bắt đầu huấn luyện.');
    } finally {
      setTraining(false);
      setTimeout(fetchStatus, 3000);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Bot className="w-8 h-8 text-indigo-500" />
            ML Control Center
          </h1>
          <p className="text-gray-500 mt-1">
            Theo dõi dữ liệu học máy và huấn luyện mô hình XGBoost dự đoán CTR.
          </p>
        </div>
        <button
          onClick={fetchStatus}
          className="p-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-gray-600 transition-colors"
          title="Làm mới trạng thái"
        >
          <RefreshCw className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {message && (
        <div className="p-4 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-100">
          {message}
        </div>
      )}

      {status ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center gap-4">
            <div className="p-4 bg-blue-50 rounded-full text-blue-500">
              <Database className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Dữ liệu huấn luyện</p>
              <h2 className="text-3xl font-bold text-gray-800">{status.interaction_count}</h2>
              <p className="text-xs text-gray-400 mt-1">Lượt tương tác FoodInteraction</p>
            </div>
          </div>

          <div className="bg-white p-6 rounded-xl border border-gray-100 shadow-sm flex items-center gap-4">
            <div className={`p-4 rounded-full ${status.is_model_loaded ? 'bg-green-50 text-green-500' : 'bg-orange-50 text-orange-500'}`}>
              <Activity className="w-8 h-8" />
            </div>
            <div>
              <p className="text-sm font-medium text-gray-500 uppercase tracking-wider">Trạng thái Ranker</p>
              <h2 className={`text-xl font-bold ${status.is_model_loaded ? 'text-green-600' : 'text-orange-500'}`}>
                {status.active_ranker}
              </h2>
              <p className="text-xs text-gray-400 mt-1">
                {status.is_model_loaded ? `Đã nạp: ${status.model_path}` : 'Mô hình XGBoost chưa được huấn luyện'}
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div className="text-center py-10 text-gray-400">Đang tải trạng thái...</div>
      )}

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-gray-100">
          <h3 className="text-lg font-bold text-gray-800">Auto-ML Training Pipeline</h3>
          <p className="text-sm text-gray-500 mt-1">
            Khi dữ liệu tương tác đủ lớn, bạn có thể kích hoạt trích xuất đặc trưng và huấn luyện XGBoost.
          </p>
        </div>
        <div className="p-6 bg-gray-50 flex items-center justify-between gap-6">
          <div className="text-sm text-gray-600">
            <strong>Lưu ý:</strong> Quá trình huấn luyện chạy nền và không ảnh hưởng đến trải nghiệm người dùng.
          </div>
          <button
            onClick={handleTrain}
            disabled={training || (status && status.interaction_count < 10)}
            className="px-6 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium rounded-lg shadow-sm transition-all flex items-center gap-2 whitespace-nowrap"
          >
            {training ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Đang huấn luyện...
              </>
            ) : (
              <>
                <Bot className="w-5 h-5" />
                Bắt đầu huấn luyện
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

export default MLControlCenter;
