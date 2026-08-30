import { useEffect, useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  ShoppingBag, Package, TrendingUp, Users, DollarSign,
  CheckCircle, Clock, XCircle, Search, RefreshCw,
  MapPin, Star, AlertCircle, Eye
} from 'lucide-react';
import './AdminTheme.css';
import './AdminPanelAdvanced.css';

const API_BASE = 'http://localhost:8000/api/v1';

export default function MarketplaceDashboard() {
  const [products, setProducts] = useState<any[]>([]);
  const [orders, setOrders] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchAll = async () => {
    try {
      const token = localStorage.getItem('access_token');
      const headers = { Authorization: 'Bearer ' + token };

      const [prodRes, ordRes, statsRes] = await Promise.all([
        fetch(API_BASE + '/marketplace/products', { headers }),
        fetch(API_BASE + '/marketplace/orders', { headers }),
        fetch(API_BASE + '/marketplace/stats', { headers }),
      ]);

      if (prodRes.ok) {
        const data = await prodRes.json();
        setProducts(Array.isArray(data) ? data : data.items || []);
      }
      if (ordRes.ok) {
        const data = await ordRes.json();
        setOrders(Array.isArray(data) ? data : data.items || []);
      }
      if (statsRes.ok) {
        setStats(await statsRes.json());
      }
    } catch (e) {
      console.error('Failed to fetch marketplace data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchAll(); }, []);

  const confirmOrder = async (orderId: string) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await fetch(API_BASE + '/marketplace/orders/' + orderId + '/confirm', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token },
      });
      if (res.ok) fetchAll();
    } catch (e) {
      console.error('Failed to confirm order:', e);
    }
  };

  const COLORS = ['#10b981', '#f59e0b', '#3b82f6', '#8b5cf6', '#ef4444'];

  const filteredProducts = searchQuery
    ? products.filter(p =>
        (p.name || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.producer || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : products;

  if (loading) {
    return (
      <div className="admin-page-container">
        <div className="page-header">
          <div>
            <h1 className="page-title"><ShoppingBag size={32} /> Marketplace Dashboard</h1>
            <p className="page-subtitle">Loading marketplace data...</p>
          </div>
        </div>
        <div className="grid-4col">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="metric-card">
              <div className="skeleton skeleton-title"></div>
              <div className="skeleton skeleton-card"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  const pendingOrders = orders.filter(o => (o.status || '').toLowerCase() === 'pending');
  const completedOrders = orders.filter(o => (o.status || '').toLowerCase() === 'confirmed' || (o.status || '').toLowerCase() === 'completed');

  // Calculate stats
  const totalRevenue = orders.reduce((sum, o) => sum + (o.total || o.amount || 0), 0);
  const avgOrderValue = orders.length > 0 ? totalRevenue / orders.length : 0;

  // Orders by status for pie chart
  const ordersByStatus = orders.reduce((acc: any, o) => {
    const status = o.status || 'unknown';
    acc[status] = (acc[status] || 0) + 1;
    return acc;
  }, {});
  const pieData = Object.entries(ordersByStatus).map(([name, value]) => ({ name, value }));

  return (
    <div className="admin-page-container">
      {/* Header */}
      <div className="page-header">
        <div>
          <h1 className="page-title">
            <ShoppingBag size={32} style={{ color: 'var(--accent-primary)' }} />
            Marketplace Dashboard
          </h1>
          <p className="page-subtitle">
            Monitor products, orders, and marketplace performance
          </p>
        </div>
        <button className="refresh-btn" onClick={fetchAll}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid-4col">
        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: 'var(--accent-primary)' }}>
            <Package size={28} />
          </div>
          <div className="metric-label">Total Products</div>
          <div className="metric-value">{products.length}</div>
          <div className="metric-change positive">
            <TrendingUp size={12} /> Active
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent-info)' }}>
            <ShoppingBag size={28} />
          </div>
          <div className="metric-label">Total Orders</div>
          <div className="metric-value">{orders.length}</div>
          <div className="metric-change positive">
            <Clock size={12} /> {pendingOrders.length} pending
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: 'var(--accent-secondary)' }}>
            <DollarSign size={28} />
          </div>
          <div className="metric-label">Total Revenue</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {totalRevenue.toLocaleString('fa-IR')} IRR
          </div>
          <div className="metric-change positive">
            <TrendingUp size={12} /> +18%
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon" style={{ background: 'rgba(139, 92, 246, 0.15)', color: 'var(--accent-purple)' }}>
            <Star size={28} />
          </div>
          <div className="metric-label">Avg Order Value</div>
          <div className="metric-value" style={{ fontSize: '24px' }}>
            {avgOrderValue.toLocaleString('fa-IR', { maximumFractionDigits: 0 })} IRR
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid-2col">
        {/* Orders by Status */}
        <div className="chart-container">
          <div className="chart-title">
            <ShoppingBag size={20} />
            Orders by Status
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => name + ' ' + ((percent || 0) * 100).toFixed(0) + '%'}
                outerRadius={90}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={'cell-' + index} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card-solid)',
                  border: '1px solid var(--border-color)',
                  borderRadius: '8px',
                  color: 'var(--text-primary)',
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Pending Orders Alert */}
        <div className="chart-container">
          <div className="chart-title">
            <AlertCircle size={20} />
            Pending Orders ({pendingOrders.length})
          </div>
          <div style={{ maxHeight: '280px', overflowY: 'auto' }}>
            {pendingOrders.length === 0 ? (
              <div className="empty-state-enhanced" style={{ padding: '40px 20px' }}>
                <div className="icon" style={{ fontSize: '48px' }}>✅</div>
                <div className="title">All caught up!</div>
                <div>No pending orders</div>
              </div>
            ) : (
              pendingOrders.slice(0, 5).map((order: any) => (
                <div key={order.id} className="transaction-row" style={{ borderBottom: '1px solid var(--border-color)' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, color: 'var(--text-primary)', fontSize: '14px' }}>
                      Order #{order.id?.substring(0, 8) || 'N/A'}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {(order.total || order.amount || 0).toLocaleString('fa-IR')} IRR
                    </div>
                  </div>
                  <button
                    className="btn-primary"
                    style={{ padding: '6px 14px', fontSize: '12px' }}
                    onClick={() => confirmOrder(order.id)}
                  >
                    <CheckCircle size={14} style={{ marginRight: '4px' }} /> Confirm
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Products Table */}
      <div className="chart-container">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div className="chart-title" style={{ margin: 0 }}>
            <Package size={20} />
            Products Catalog
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ position: 'relative' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
              <input
                type="text"
                placeholder="Search products..."
                className="form-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{ paddingLeft: '36px', width: '250px' }}
              />
            </div>
          </div>
        </div>

        <table className="admin-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Producer</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredProducts.length === 0 ? (
              <tr>
                <td colSpan={6}>
                  <div className="empty-state-enhanced">
                    <div className="icon">📦</div>
                    <div className="title">No products found</div>
                    <div>{searchQuery ? 'Try a different search' : 'No products in catalog'}</div>
                  </div>
                </td>
              </tr>
            ) : (
              filteredProducts.slice(0, 10).map((product: any, i: number) => (
                <tr key={product.id || i}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '40px', height: '40px', borderRadius: '10px',
                        background: 'linear-gradient(135deg, var(--accent-primary), var(--accent-secondary))',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        color: 'white', fontSize: '18px',
                      }}>
                        🌾
                      </div>
                      <div>
                        <div style={{ fontWeight: 600, color: 'var(--text-primary)' }}>{product.name || 'Unnamed'}</div>
                        <div style={{ fontSize: '12px', color: 'var(--text-faint)' }}>ID: {product.id?.substring(0, 8) || 'N/A'}</div>
                      </div>
                    </div>
                  </td>
                  <td style={{ color: 'var(--text-secondary)' }}>{product.producer || '-'}</td>
                  <td style={{ fontWeight: 600, color: 'var(--accent-primary)' }}>
                    {(product.price || 0).toLocaleString('fa-IR')} IRR
                  </td>
                  <td>{product.stock !== undefined ? product.stock : '-'}</td>
                  <td>
                    <span className="status-badge success">Active</span>
                  </td>
                  <td>
                    <button className="btn-secondary" style={{ padding: '6px 12px', fontSize: '11px' }}>
                      <Eye size={12} style={{ marginRight: '4px' }} /> Trace
                    </button>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
