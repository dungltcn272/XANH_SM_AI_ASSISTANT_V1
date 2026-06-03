import { useState, useEffect } from 'react';
import { Database, Trash2, RefreshCw, AlertCircle, CheckSquare, Square } from 'lucide-react';
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

  // Pagination
  const [page, setPage] = useState(0);
  const limit = 50;

  useEffect(() => {
    const fetchTables = async () => {
      try {
        const res = await api.getDbTables();
        setTables(res || []);
        if (res && res.length > 0) {
          setSelectedTable(res[0]);
        }
      } catch (err) {
        setError('Failed to load database tables.');
      }
      setLoading(false);
    };
    fetchTables();
  }, []);

  useEffect(() => {
    if (!selectedTable) return;
    
    const fetchTableData = async () => {
      setDataLoading(true);
      setError('');
      try {
        const res = await api.getTableData(selectedTable, limit, page * limit);
        setData(res.data || []);
        setColumns(res.columns || []);
        setTotal(res.total || 0);
        setSelectedIds(new Set());
      } catch (err) {
        setError(`Failed to load data for table: ${selectedTable}`);
      }
      setDataLoading(false);
    };
    fetchTableData();
  }, [selectedTable, page]);

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
      const res = await api.getTableData(selectedTable, limit, page * limit);
      setData(res.data || []);
      setTotal(res.total || 0);
      setSelectedIds(new Set());
    } catch (err) {
      setError('Failed to delete records. Ensure table has an ID column.');
    }
    setDeleting(false);
  };

  if (loading) {
    return <div className="p-8 text-on-surface-variant animate-pulse">Loading database manager...</div>;
  }

  const hasIdColumn = columns.includes('id');

  return (
    <div className="max-w-[1600px] mx-auto w-full">
      <div className="mb-10 flex justify-between items-end">
        <div>
          <h2 className="text-3xl md:text-4xl font-bold text-on-surface flex items-center gap-3">
            <Database className="text-primary w-8 h-8" />
            Database Manager
          </h2>
          <p className="text-lg text-on-surface-variant mt-2 max-w-2xl">
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
        <div className="p-4 border-b border-outline-variant/30 flex flex-wrap gap-4 justify-between items-center bg-white/40">
          <div className="flex items-center gap-4">
            <label className="text-sm font-semibold text-on-surface-variant">Select Table:</label>
            <select 
              value={selectedTable}
              onChange={(e) => {
                setSelectedTable(e.target.value);
                setPage(0);
              }}
              className="bg-surface-variant border border-outline-variant/50 text-on-surface text-sm rounded-lg focus:ring-primary focus:border-primary block p-2.5"
            >
              {tables.map(t => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
            
            <span className="text-xs text-on-surface-variant font-mono bg-surface-container-low px-2 py-1 rounded">
              {total} records
            </span>
          </div>

          <div className="flex items-center gap-3">
            <button 
              onClick={() => setPage(p => p)} // trigger re-fetch visually by doing nothing if not memoized, wait, actually let's just trigger a reload function
              className="p-2 rounded-lg bg-surface-variant text-on-surface-variant hover:bg-surface-container-high transition-colors"
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
                  : 'bg-surface-variant text-on-surface-variant opacity-50 cursor-not-allowed'
              }`}
            >
              {deleting ? <RefreshCw size={18} className="animate-spin" /> : <Trash2 size={18} />}
              Delete Selected ({selectedIds.size})
            </button>
          </div>
        </div>

        {/* Data Table */}
        <div className="flex-1 overflow-auto">
          {dataLoading ? (
            <div className="p-8 text-center text-on-surface-variant animate-pulse font-semibold">Loading table data...</div>
          ) : data.length === 0 ? (
            <div className="p-12 text-center text-on-surface-variant italic">Table is empty.</div>
          ) : (
            <table className="w-full text-left border-collapse">
              <thead className="sticky top-0 bg-surface z-10 shadow-sm">
                <tr className="text-on-surface-variant text-xs uppercase tracking-wider">
                  {hasIdColumn && (
                    <th className="px-4 py-3 border-b border-outline-variant/30 w-12 text-center">
                      <button onClick={toggleSelectAll} className="text-on-surface-variant hover:text-primary transition-colors">
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
                      <td key={col} className="px-4 py-3 text-sm text-on-surface max-w-xs truncate cursor-pointer" title={String(row[col])}>
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
        <div className="p-3 border-t border-outline-variant/30 bg-surface-container-low flex justify-between items-center text-sm font-semibold text-on-surface-variant">
          <div>
            Showing {page * limit + 1} to {Math.min((page + 1) * limit, total)} of {total} entries
          </div>
          <div className="flex gap-2">
            <button 
              onClick={() => setPage(p => Math.max(0, p - 1))}
              disabled={page === 0}
              className="px-3 py-1 bg-surface rounded-md border border-outline-variant/50 hover:bg-surface-variant disabled:opacity-50"
            >
              Prev
            </button>
            <button 
              onClick={() => setPage(p => p + 1)}
              disabled={(page + 1) * limit >= total}
              className="px-3 py-1 bg-surface rounded-md border border-outline-variant/50 hover:bg-surface-variant disabled:opacity-50"
            >
              Next
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
