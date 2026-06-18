import { useState, useEffect } from 'react';
import { Database, Search, Trash2, RefreshCw, AlertCircle, CheckSquare, Square, X } from 'lucide-react';
import { api } from '../api';

export default function DatabaseManager() {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState('');
  
  const [data, setData] = useState([]);
  const [columns, setColumns] = useState([]);
  const [total, setTotal] = useState(0);
  
  const [loading, setLoading] = useState(true);
  const [dataLoading, setDataLoading] = useState(false);
  const [error, setError] = useState('');
  
  const [selectedIds, setSelectedIds] = useState(new Set());
  const [deleting, setDeleting] = useState(false);

  // Sorting & Filtering States
  const [sortBy, setSortBy] = useState('');
  const [sortOrder, setSortOrder] = useState('desc');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [level, setLevel] = useState('');
  const [errorType, setErrorType] = useState('');
  const [keyword, setKeyword] = useState('');
  const [debouncedKeyword, setDebouncedKeyword] = useState('');
  const [metadata, setMetadata] = useState({});

  // Pagination
  const [page, setPage] = useState(0);
  const [pageInput, setPageInput] = useState('1');
  const limit = 50;

  const changePage = (targetPage) => {
    setPage(targetPage);
    setPageInput((targetPage + 1).toString());
  };

  useEffect(() => {
    const fetchTables = async () => {
      try {
        const res = await api.getDbTables();
        setTables(res || []);
        if (res && res.length > 0) {
          setSelectedTable(res[0]);
        }
      } catch {
        setError('Failed to load database tables.');
      }
      setLoading(false);
    };
    fetchTables();
  }, []);

  useEffect(() => {
    const timeout = setTimeout(() => {
      setDebouncedKeyword(keyword.trim());
      changePage(0);
    }, 350);

    return () => clearTimeout(timeout);
  }, [keyword]);

  useEffect(() => {
    if (!selectedTable) return;
    
    const fetchTableData = async () => {
      setDataLoading(true);
      setError('');
      try {
        const filters = {
          sort_by: sortBy,
          sort_order: sortOrder,
          start_date: startDate,
          end_date: endDate,
          level: level,
          error_type: errorType,
          keyword: debouncedKeyword
        };
        const res = await api.getTableData(selectedTable, limit, page * limit, filters);
        setData(res.data || []);
        setColumns(res.columns || []);
        setTotal(res.total || 0);
        setMetadata(res.metadata || {});
        setSelectedIds(new Set());
      } catch {
        setError(`Failed to load data for table: ${selectedTable}`);
      }
      setDataLoading(false);
    };
    fetchTableData();
  }, [selectedTable, page, sortBy, sortOrder, startDate, endDate, level, errorType, debouncedKeyword]);

  const toggleSelectAll = () => {
    if (selectedIds.size === data.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(data.map(row => row.id)));
    }
  };

  const toggleSelectRow = (id) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedIds(newSelected);
  };

  const handleDeleteSelected = async () => {
    if (selectedIds.size === 0) return;
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.size} record(s)?`)) return;
    
    setDeleting(true);
    try {
      await api.deleteTableData(selectedTable, Array.from(selectedIds));
      // Refresh data
      const filters = {
        sort_by: sortBy,
        sort_order: sortOrder,
        start_date: startDate,
        end_date: endDate,
        level: level,
        error_type: errorType,
        keyword: debouncedKeyword
      };
      const res = await api.getTableData(selectedTable, limit, page * limit, filters);
      setData(res.data || []);
      setTotal(res.total || 0);
      setSelectedIds(new Set());
    } catch {
      setError('Failed to delete records. Ensure table has an ID column.');
    }
    setDeleting(false);
  };

  const handleDeleteAll = async () => {
    if (!selectedTable) return;
    const confirm1 = window.confirm(`BẠN CÓ CHẮC CHẮN MUỐN XÓA TOÀN BỘ BẢN GHI CỦA BẢNG "${selectedTable}"?\nHành động này sẽ xóa sạch tất cả các dòng dữ liệu và KHÔNG THỂ HOÀN TÁC!`);
    if (!confirm1) return;
    
    const confirm2 = window.prompt(`Để xác nhận xóa toàn bộ bảng, vui lòng nhập chính xác tên bảng: "${selectedTable}"`);
    if (confirm2 !== selectedTable) {
      alert("Xác thực tên bảng không chính xác. Đã hủy bỏ thao tác xóa toàn bộ.");
      return;
    }
    
    setDeleting(true);
    try {
      await api.deleteAllTableData(selectedTable);
      alert(`Đã xóa toàn bộ dữ liệu của bảng "${selectedTable}" thành công.`);
      changePage(0);
      // Refresh
      const res = await api.getTableData(selectedTable, limit, 0, {});
      setData(res.data || []);
      setTotal(res.total || 0);
      setSelectedIds(new Set());
    } catch {
      setError(`Failed to delete all records for table: ${selectedTable}`);
    }
    setDeleting(false);
  };

  // Pagination input handlers
  const handlePageInputChange = (e) => {
    setPageInput(e.target.value);
  };

  const handlePageInputSubmit = () => {
    let targetPage = parseInt(pageInput, 10);
    const totalPages = Math.ceil(total / limit) || 1;
    
    if (isNaN(targetPage) || targetPage < 1) {
      targetPage = 1;
    } else if (targetPage > totalPages) {
      targetPage = totalPages;
    }
    
    changePage(targetPage - 1);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handlePageInputSubmit();
    }
  };

  if (loading) {
    return <div className="p-8 text-[#94a3b8] animate-pulse">Loading database manager...</div>;
  }

  const hasIdColumn = columns.includes('id');
  const totalPages = Math.ceil(total / limit) || 1;

  return (
    <div className="max-w-[1600px] mx-auto w-full">
      <div className="mb-10 flex justify-between items-end">
        <div>
          <h2 className="text-3xl md:text-4xl font-bold text-white flex items-center gap-3">
            <Database className="text-primary w-8 h-8" />
            Database Manager
          </h2>
          <p className="text-lg text-[#94a3b8] mt-2 max-w-2xl">
            Direct access to raw SQL tables. Handle with care.
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded-xl bg-error-container text-on-error-container flex items-center gap-3 font-semibold border border-error/20">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      <div className="glass-panel rounded-3xl overflow-hidden border border-outline-variant/30 flex flex-col h-[70vh]">
        {/* Toolbar */}
        <div className="p-4 border-b border-outline-variant/30 flex flex-wrap gap-4 justify-between items-center bg-[#0f1520]">
          <div className="flex items-center gap-4">
            <label className="text-sm font-semibold text-[#94a3b8]">Select Table:</label>
            <select 
              value={selectedTable}
              onChange={(e) => {
                setSelectedTable(e.target.value);
                setSortBy('');
                setSortOrder('desc');
                setStartDate('');
                setEndDate('');
                setLevel('');
                setErrorType('');
                setKeyword('');
                setDebouncedKeyword('');
                changePage(0);
              }}
              className="bg-[#022c22] border border-outline-variant/50 text-white text-sm rounded-lg focus:ring-primary focus:border-primary block py-2.5 pl-2.5 pr-10 cursor-pointer"
            >
              {tables.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            
            <span className="text-xs text-[#94a3b8] font-mono bg-[#0f1520]-container-low px-2 py-1 rounded">
              {total} records
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => {
                // Refresh table content
                setDataLoading(true);
                const filters = {
                  sort_by: sortBy,
                  sort_order: sortOrder,
                  start_date: startDate,
                  end_date: endDate,
                  level: level,
                  error_type: errorType,
                  keyword: debouncedKeyword
                };
                api.getTableData(selectedTable, limit, page * limit, filters).then(res => {
                  setData(res.data || []);
                  setTotal(res.total || 0);
                  setSelectedIds(new Set());
                }).catch(() => setError('Failed to refresh table')).finally(() => setDataLoading(false));
              }}
              className="p-2 rounded-lg bg-[#022c22] text-[#94a3b8] hover:bg-[#0f1520]-container-high transition-colors"
              title="Refresh"
            >
              <RefreshCw size={18} className={dataLoading ? "animate-spin" : ""} />
            </button>

            <button
              onClick={handleDeleteSelected}
              disabled={selectedIds.size === 0 || deleting || !hasIdColumn}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all shadow-sm ${
                selectedIds.size > 0 && hasIdColumn
                  ? 'bg-error text-white hover:bg-error/90 hover:shadow-md'
                  : 'bg-[#022c22] text-[#94a3b8] opacity-50 cursor-not-allowed'
              }`}
            >
              {deleting ? <RefreshCw size={18} className="animate-spin" /> : <Trash2 size={18} />}
              Delete Selected ({selectedIds.size})
            </button>

            <button
              onClick={handleDeleteAll}
              disabled={deleting || total === 0}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold transition-all shadow-sm ${
                total > 0
                  ? 'bg-red-600 hover:bg-red-700 text-white hover:shadow-md'
                  : 'bg-[#022c22] text-[#94a3b8] opacity-50 cursor-not-allowed'
              }`}
              title="Xóa toàn bộ bản ghi của bảng"
            >
              {deleting ? <RefreshCw size={18} className="animate-spin" /> : <Trash2 size={18} />}
              Delete All
            </button>
          </div>
        </div>

        {/* Filter Panel (Dynamic based on selected table columns) */}
        <div className="px-4 py-3 border-b border-outline-variant/20 bg-[#0f1520]-container-lowest/50 flex flex-wrap gap-4 items-center">
          {/* Keyword Search */}
          <div className="flex items-center gap-2 min-w-[260px] flex-1 max-w-md">
            <span className="text-xs font-semibold text-[#94a3b8]">Từ khóa:</span>
            <div className="relative flex-1">
              <Search size={15} className="absolute left-2.5 top-1/2 -translate-y-1/2 text-[#94a3b8]" />
              <input
                type="search"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Tìm trong content, description, message..."
                className="w-full bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg py-2 pl-8 pr-8 focus:ring-primary focus:border-primary"
              />
              {keyword && (
                <button
                  onClick={() => {
                    setKeyword('');
                    setDebouncedKeyword('');
                    changePage(0);
                  }}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-[#94a3b8] hover:text-white"
                  title="XÃ³a tá»« khÃ³a"
                >
                  <X size={15} />
                </button>
              )}
            </div>
          </div>

          {/* Sorting */}
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-[#94a3b8]">Sắp xếp:</span>
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); changePage(0); }}
              className="bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg py-2 pl-2 pr-8 focus:ring-primary focus:border-primary cursor-pointer"
            >
              <option value="">-- Mặc định --</option>
              {columns.map(col => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
            <select
              value={sortOrder}
              onChange={(e) => { setSortOrder(e.target.value); changePage(0); }}
              className="bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg py-2 pl-2 pr-8 focus:ring-primary focus:border-primary cursor-pointer"
            >
              <option value="desc">Giảm dần (Mới nhất)</option>
              <option value="asc">Tăng dần (Cũ nhất)</option>
            </select>
          </div>

          {/* Date range filter (conditional) */}
          {columns.some(c => ['created_at', 'timestamp', 'generated_at'].includes(c)) && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#94a3b8]">Khoảng ngày:</span>
              <input
                type="date"
                value={startDate}
                onChange={(e) => { setStartDate(e.target.value); changePage(0); }}
                className="bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg p-1.5 focus:ring-primary focus:border-primary text-center"
              />
              <span className="text-xs text-[#94a3b8]">đến</span>
              <input
                type="date"
                value={endDate}
                onChange={(e) => { setEndDate(e.target.value); changePage(0); }}
                className="bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg p-1.5 focus:ring-primary focus:border-primary text-center"
              />
            </div>
          )}

          {/* Level filter (conditional for logs) */}
          {columns.includes('level') && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#94a3b8]">Level:</span>
              <select
                value={level}
                onChange={(e) => { setLevel(e.target.value); changePage(0); }}
                className="bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg py-2 pl-2 pr-8 focus:ring-primary focus:border-primary cursor-pointer"
              >
                <option value="">Tất cả</option>
                {(metadata.levels || ['INFO', 'WARN', 'ERROR']).map(l => (
                  <option key={l} value={l}>{l}</option>
                ))}
              </select>
            </div>
          )}

          {/* Error Type filter (conditional for logs) */}
          {columns.includes('error_type') && (
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-[#94a3b8]">Loại lỗi:</span>
              <select
                value={errorType}
                onChange={(e) => { setErrorType(e.target.value); changePage(0); }}
                className="bg-[#022c22] border border-outline-variant/40 text-white text-xs rounded-lg py-2 pl-2 pr-8 focus:ring-primary focus:border-primary max-w-xs cursor-pointer"
              >
                <option value="">Tất cả</option>
                {(metadata.error_types || []).map(et => (
                  <option key={et} value={et}>{et}</option>
                ))}
              </select>
            </div>
          )}

          {/* Reset Filters button */}
          {(sortBy || startDate || endDate || level || errorType || keyword) && (
            <button
              onClick={() => {
                setSortBy('');
                setSortOrder('desc');
                setStartDate('');
                setEndDate('');
                setLevel('');
                setErrorType('');
                setKeyword('');
                setDebouncedKeyword('');
                changePage(0);
              }}
              className="text-xs font-bold text-primary hover:underline ml-auto"
            >
              Xóa bộ lọc
            </button>
          )}
        </div>

        {/* Data Table */}
        <div className="flex-1 overflow-auto">
          {dataLoading ? (
            <div className="p-8 text-center text-[#94a3b8] animate-pulse font-semibold">Loading table data...</div>
          ) : data.length === 0 ? (
            <div className="p-12 text-center text-[#94a3b8] italic">Table is empty.</div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-[#0f1520] z-10 shadow-sm">
                <tr className="text-[#94a3b8] text-xs uppercase tracking-wider">
                  {hasIdColumn && (
                    <th className="px-4 py-3 border-b border-outline-variant/30 w-12 text-center">
                      <button onClick={toggleSelectAll} className="text-[#94a3b8] hover:text-primary transition-colors">
                        {selectedIds.size === data.length ? <CheckSquare size={18} /> : <Square size={18} />}
                      </button>
                    </th>
                  )}
                  {columns.map(col => (
                    <th key={col} className="px-4 py-3 font-semibold border-b border-outline-variant/30 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/20">
                {data.map((row, idx) => (
                  <tr 
                    key={row.id || idx} 
                    className={`hover:bg-primary/5 transition-colors ${selectedIds.has(row.id) ? 'bg-primary/10' : ''}`}
                    onClick={() => hasIdColumn && toggleSelectRow(row.id)}
                  >
                    {hasIdColumn && (
                      <td className="px-4 py-3 text-center cursor-pointer">
                        {selectedIds.has(row.id) ? (
                          <CheckSquare size={18} className="text-primary inline-block" />
                        ) : (
                          <Square size={18} className="text-outline-variant inline-block" />
                        )}
                      </td>
                    )}
                    {columns.map(col => (
                      <td key={col} className="px-4 py-3 text-sm text-white max-w-xs truncate cursor-pointer" title={String(row[col])}>
                        {typeof row[col] === 'object' && row[col] !== null 
                          ? JSON.stringify(row[col]) 
                          : String(row[col] ?? '')}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        
        {/* Pagination Footer */}
        <div className="p-3 border-t border-outline-variant/30 bg-[#0f1520]-container-low flex justify-between items-center text-sm font-semibold text-[#94a3b8]">
          <div>
            Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of {total} entries
          </div>
          
          <div className="flex items-center gap-4">
            <button 
              onClick={() => changePage(Math.max(0, page - 1))}
              disabled={page === 0}
              className="px-3 py-1 bg-[#0f1520] rounded-md border border-outline-variant/50 hover:bg-[#022c22] disabled:opacity-50"
            >
              Prev
            </button>

            <div className="flex items-center gap-1.5 text-xs text-[#94a3b8] font-medium">
              <span>Trang</span>
              <input
                type="number"
                min="1"
                max={totalPages}
                value={pageInput}
                onChange={handlePageInputChange}
                onBlur={handlePageInputSubmit}
                onKeyDown={handleKeyDown}
                className="w-14 px-2 py-1 text-center bg-[#0f1520] border border-outline-variant/60 rounded-md focus:outline-none focus:border-primary text-white font-semibold"
              />
              <span>/ {totalPages}</span>
            </div>

            <button 
              onClick={() => changePage(page + 1)}
              disabled={(page + 1) * limit >= total}
              className="px-3 py-1 bg-[#0f1520] rounded-md border border-outline-variant/50 hover:bg-[#022c22] disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
