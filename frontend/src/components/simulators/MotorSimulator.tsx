/**
 * MotorSimulator - Reusable component for running scientific motors
 * Works with all 21 scientific motors in the system
 */

import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts';
import {
  Play, RotateCcw, Loader2, CheckCircle, AlertCircle,
  Settings, TrendingUp, Database, Zap, Info, X
} from 'lucide-react';
import motorsService, { Motor, MotorParameter } from '../../services/motorsService';
import './MotorSimulator.css';

interface MotorSimulatorProps {
  motor: Motor;
  onClose?: () => void;
  onResult?: (result: any) => void;
}

type RunStatus = 'idle' | 'running' | 'completed' | 'error';

interface RunResult {
  status: RunStatus;
  data?: any;
  error?: string;
  duration?: number;
}

export default function MotorSimulator({ motor, onClose, onResult }: MotorSimulatorProps) {
  const { t } = useTranslation();
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [runStatus, setRunStatus] = useState<RunStatus>('idle');
  const [result, setResult] = useState<RunResult | null>(null);
  const [chartData, setChartData] = useState<any[]>([]);
  const [progress, setProgress] = useState(0);

  // Initialize parameters with defaults
  useEffect(() => {
    if (motor.parameters) {
      const defaults: Record<string, any> = {};
      motor.parameters.forEach(param => {
        if (param.default !== undefined) {
          defaults[param.name] = param.default;
        }
      });
      setParameters(defaults);
    }
  }, [motor]);

  const handleParameterChange = (name: string, value: any) => {
    setParameters(prev => ({ ...prev, [name]: value }));
  };

  const handleRun = async () => {
    setRunStatus('running');
    setProgress(0);
    setResult(null);

    try {
      const startTime = Date.now();
      
      // Run the motor
      const response = await motorsService.runMotor({
        motor_key: motor.key,
        parameters,
      });

      const duration = Date.now() - startTime;

      setResult({
        status: 'completed',
        data: response.result || response,
        duration,
      });

      setRunStatus('completed');
      setProgress(100);

      // Generate chart data if available
      if (response.result && typeof response.result === 'object') {
        const chart = generateChartData(response.result);
        setChartData(chart);
      }

      if (onResult) {
        onResult(response.result);
      }
    } catch (error) {
      setResult({
        status: 'error',
        error: error instanceof Error ? error.message : String(error),
      });
      setRunStatus('error');
    }
  };

  const generateChartData = (data: any): any[] => {
    // If data is already an array, use it
    if (Array.isArray(data)) {
      return data;
    }

    // If data has time series, convert it
    if (data.timeseries || data.results || data.outputs) {
      const series = data.timeseries || data.results || data.outputs;
      if (Array.isArray(series)) {
        return series.map((item: any, index: number) => ({
          ...item,
          index,
        }));
      }
    }

    // If data is object with numeric values, convert to chart format
    if (typeof data === 'object' && data !== null) {
      return Object.entries(data)
        .filter(([_, value]) => typeof value === 'number')
        .map(([key, value]) => ({ name: key, value }));
    }

    return [];
  };

  const handleReset = () => {
    setRunStatus('idle');
    setResult(null);
    setChartData([]);
    setProgress(0);
  };

  const renderInput = (param: MotorParameter) => {
    const value = parameters[param.name] ?? param.default ?? '';

    switch (param.type) {
      case 'number':
        return (
          <input
            type="number"
            className="form-input"
            value={value}
            min={param.min}
            max={param.max}
            onChange={(e) => handleParameterChange(param.name, parseFloat(e.target.value) || 0)}
          />
        );
      case 'boolean':
        return (
          <div
            className={'toggle-switch' + (value ? ' active' : '')}
            onClick={() => handleParameterChange(param.name, !value)}
          />
        );
      case 'select':
        return (
          <select
            className="form-input"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
          >
            {(param.options || []).map(opt => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        );
      case 'string':
      default:
        return (
          <input
            type="text"
            className="form-input"
            value={value}
            onChange={(e) => handleParameterChange(param.name, e.target.value)}
          />
        );
    }
  };

  return (
    <div className="motor-simulator">
      {/* Header */}
      <div className="simulator-header">
        <div className="simulator-title-section">
          <h2 className="simulator-title">{motor.name}</h2>
          <p className="simulator-description">{motor.description}</p>
        </div>
        {onClose && (
          <button className="simulator-close" onClick={onClose}>
            <X size={20} />
          </button>
        )}
      </div>

      {/* Content Grid */}
      <div className="simulator-grid">
        {/* Parameters Panel */}
        <div className="simulator-panel">
          <div className="panel-header">
            <Settings size={18} />
            <span>{t('simulator.parameters', 'Parameters')}</span>
          </div>

          <div className="panel-content">
            {motor.parameters?.map(param => (
              <div key={param.name} className="parameter-group">
                <label className="parameter-label">
                  {param.name}
                  {param.description && (
                    <span className="parameter-hint" title={param.description}>
                      <Info size={12} />
                    </span>
                  )}
                </label>
                {renderInput(param)}
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="simulator-actions">
            <button
              className="btn-primary"
              onClick={handleRun}
              disabled={runStatus === 'running'}
            >
              {runStatus === 'running' ? (
                <>
                  <Loader2 size={16} className="spin" />
                  {t('simulator.running', 'Running...')}
                </>
              ) : (
                <>
                  <Play size={16} />
                  {t('simulator.run', 'Run Simulation')}
                </>
              )}
            </button>

            <button
              className="btn-secondary"
              onClick={handleReset}
              disabled={runStatus === 'running'}
            >
              <RotateCcw size={16} />
              {t('simulator.reset', 'Reset')}
            </button>
          </div>

          {/* Progress Bar */}
          {runStatus === 'running' && (
            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${progress}%` }} />
            </div>
          )}
        </div>

        {/* Results Panel */}
        <div className="simulator-panel">
          <div className="panel-header">
            <TrendingUp size={18} />
            <span>{t('simulator.results', 'Results')}</span>
          </div>

          <div className="panel-content">
            {runStatus === 'idle' && (
              <div className="empty-state">
                <Database size={48} style={{ opacity: 0.3 }} />
                <p>{t('simulator.runFirst', 'Run simulation to see results')}</p>
              </div>
            )}

            {runStatus === 'running' && (
              <div className="loading-state">
                <Loader2 size={48} className="spin" />
                <p>{t('simulator.runningSimulation', 'Running simulation...')}</p>
              </div>
            )}

            {runStatus === 'error' && result?.error && (
              <div className="error-state">
                <AlertCircle size={48} />
                <p>{result.error}</p>
              </div>
            )}

            {runStatus === 'completed' && (
              <div className="results-container">
                {/* Chart */}
                {chartData.length > 0 && (
                  <div className="chart-container" style={{ marginBottom: '20px' }}>
                    <ResponsiveContainer width="100%" height={250}>
                      <AreaChart data={chartData}>
                        <defs>
                          <linearGradient id="colorResult" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.8} />
                            <stop offset="95%" stopColor="#10b981" stopOpacity={0.1} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                        <XAxis dataKey={Object.keys(chartData[0] || {})[0] || 'index'} stroke="var(--text-muted)" fontSize={11} />
                        <YAxis stroke="var(--text-muted)" fontSize={11} />
                        <Tooltip
                          contentStyle={{
                            background: 'var(--bg-card-solid)',
                            border: '1px solid var(--border-color)',
                            borderRadius: '8px',
                            color: 'var(--text-primary)',
                          }}
                        />
                        <Area type="monotone" dataKey={Object.keys(chartData[0] || {})[1] || 'value'} stroke="#10b981" fillOpacity={1} fill="url(#colorResult)" />
                      </AreaChart>
                    </ResponsiveContainer>
                  </div>
                )}

                {/* Data Display */}
                <div className="data-display">
                  <pre style={{ fontSize: '12px', color: 'var(--text-muted)', overflow: 'auto', maxHeight: '300px' }}>
                    {JSON.stringify(result?.data, null, 2)}
                  </pre>
                </div>

                {/* Success Message */}
                <div className="success-message">
                  <CheckCircle size={16} />
                  <span>
                    {t('simulator.completed', 'Simulation completed')}
                    {result?.duration && ` (${result.duration}ms)`}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
