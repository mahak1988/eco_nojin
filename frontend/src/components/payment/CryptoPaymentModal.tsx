import React, { useState, useEffect, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  X, Copy, Check, Wallet, ExternalLink,
  AlertCircle, Loader2, Shield, QrCode } from 'lucide-react';
import { CRYPTO_NETWORKS, type CryptoNetwork } from '../../config/crypto';

interface CryptoPaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  amountUsd: number;
  planName: string;
  onSuccess?: (txHash: string, network: string) => void;
}

type PaymentMethod = 'wallet' | 'manual';

export const CryptoPaymentModal: React.FC<CryptoPaymentModalProps> = ({
  isOpen,
  onClose,
  amountUsd,
  planName,
  onSuccess }) => {
  const [selectedNetwork, setSelectedNetwork] = useState<CryptoNetwork>(CRYPTO_NETWORKS[0]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('manual');
  const [copied, setCopied] = useState(false);
  const [walletConnected, setWalletConnected] = useState(false);
  const [walletAddress, setWalletAddress] = useState<string>('');
  const [walletBalance, setWalletBalance] = useState<string>('0');
  const [isProcessing, setIsProcessing] = useState(false);
  const [txHash, setTxHash] = useState<string>('');
  const [error, setError] = useState<string>('');

  // ریست وضعیت وقتی modal باز می‌شود
  useEffect(() => {
    if (isOpen) {
      setTxHash('');
      setError('');
      setCopied(false);
      setIsProcessing(false);
    }
  }, [isOpen]);

  // اتصال به MetaMask / Wallet
  const connectWallet = async () => {
    setError('');
    try {
      // بررسی وجود MetaMask
      const ethereum = (window as any).ethereum;
      if (!ethereum) {
        setError('MetaMask نصب نیست. لطفاً از metamask.io نصب کنید یا از روش "کپی لینک" استفاده کنید.');
        return;
      }

      setIsProcessing(true);
      const accounts = await ethereum.request({ method: 'eth_requestAccounts' });
      if (accounts.length > 0) {
        setWalletAddress(accounts[0]);
        setWalletConnected(true);

        // دریافت موجودی
        const balance = await ethereum.request({
          method: 'eth_getBalance',
          params: [accounts[0], 'latest'] });
        const balanceEth = parseInt(balance, 16) / 1e18;
        setWalletBalance(balanceEth.toFixed(4));
      }
    } catch (err: any) {
      setError(err.message || 'خطا در اتصال کیف پول');
    } finally {
      setIsProcessing(false);
    }
  };

  // کپی آدرس
  const copyAddress = async () => {
    try {
      await navigator.clipboard.writeText(selectedNetwork.projectAddress);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError('خطا در کپی آدرس');
    }
  };

  // کپی لینک پرداخت (با مقدار)
  const copyPaymentLink = async () => {
    const link = `${selectedNetwork.symbol}:${selectedNetwork.projectAddress}?amount=${amountUsd}`;
    try {
      await navigator.clipboard.writeText(link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      setError('خطا در کپی لینک');
    }
  };

  // QR Code (SVG ساده)
  const qrDataUrl = useMemo(() => {
    // QR ساده placeholder - در production از qrcode library استفاده شود
    return `data:image/svg+xml;base64,${btoa(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200">
        <rect width="200" height="200" fill="white"/>
        <g fill="black">
          <rect x="10" y="10" width="60" height="60"/>
          <rect x="20" y="20" width="40" height="40" fill="white"/>
          <rect x="30" y="30" width="20" height="20"/>
          <rect x="130" y="10" width="60" height="60"/>
          <rect x="140" y="20" width="40" height="40" fill="white"/>
          <rect x="150" y="30" width="20" height="20"/>
          <rect x="10" y="130" width="60" height="60"/>
          <rect x="20" y="140" width="40" height="40" fill="white"/>
          <rect x="30" y="150" width="20" height="20"/>
          <text x="100" y="105" font-family="Arial" font-size="14" text-anchor="middle" fill="#333">
            QR Code
          </text>
          <text x="100" y="125" font-family="Arial" font-size="8" text-anchor="middle" fill="#666">
            ${selectedNetwork.symbol}
          </text>
        </g>
      </svg>
    `)}`;
  }, [selectedNetwork]);

  // باز کردن explorer
  const openExplorer = () => {
    if (txHash) {
      window.open(`${selectedNetwork.explorerUrl}${txHash}`, '_blank');
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          backdropFilter: 'blur(8px)',
          zIndex: 1000,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '1rem' }}
      >
        <motion.div
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          onClick={(e) => e.stopPropagation()}
          className="card"
          style={{
            maxWidth: 600,
            width: '100%',
            maxHeight: '90vh',
            overflowY: 'auto',
            padding: '2rem',
            position: 'relative' }}
        >
          {/* Close Button */}
          <button
            onClick={onClose}
            className="btn btn-ghost"
            style={{
              position: 'absolute',
              top: '1rem',
              left: '1rem',
              padding: '0.5rem',
              borderRadius: '50%' }}
          >
            <X size={20} />
          </button>

          {/* Header */}
          <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
            <div
              style={{
                width: 64,
                height: 64,
                borderRadius: '50%',
                background: 'linear-gradient(135deg, var(--color-primary), var(--color-accent))',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                margin: '0 auto 1rem' }}
            >
              <Wallet size={32} />
            </div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.5rem' }}>
              پرداخت امن با رمزارز
            </h2>
            <p style={{ color: 'var(--color-text-secondary)', margin: 0 }}>
              {planName} • <strong>${amountUsd}</strong>
            </p>
          </div>

          {/* Network Selector */}
          <div style={{ marginBottom: '1.5rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 600 }}>
              شبکه را انتخاب کنید:
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
              {CRYPTO_NETWORKS.map((network) => (
                <motion.button
                  key={network.id}
                  onClick={() => setSelectedNetwork(network)}
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  style={{
                    padding: '0.75rem',
                    borderRadius: 'var(--radius-lg)',
                    border: selectedNetwork.id === network.id
                      ? `2px solid ${network.color}`
                      : '2px solid var(--color-border)',
                    background: selectedNetwork.id === network.id
                      ? `${network.color}15`
                      : 'transparent',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    fontSize: '0.875rem',
                    transition: 'all 0.2s' }}
                >
                  <span style={{ fontSize: '1.25rem' }}>{network.icon}</span>
                  <div style={{ textAlign: 'right', flex: 1 }}>
                    <div style={{ fontWeight: 600, color: 'var(--color-text-primary)' }}>
                      {network.nameFa}
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)' }}>
                      کارمزد ~${network.estimatedFeeUsd}
                    </div>
                  </div>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Payment Method Tabs */}
          <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1.5rem' }}>
            <button
              onClick={() => setPaymentMethod('wallet')}
              className="btn"
              style={{
                flex: 1,
                background: paymentMethod === 'wallet' ? 'var(--color-primary)' : 'var(--color-surface)',
                color: paymentMethod === 'wallet' ? 'white' : 'var(--color-text-secondary)' }}
            >
              <Wallet size={16} /> اتصال کیف پول
            </button>
            <button
              onClick={() => setPaymentMethod('manual')}
              className="btn"
              style={{
                flex: 1,
                background: paymentMethod === 'manual' ? 'var(--color-primary)' : 'var(--color-surface)',
                color: paymentMethod === 'manual' ? 'white' : 'var(--color-text-secondary)' }}
            >
              <Copy size={16} /> کپی آدرس
            </button>
          </div>

          {/* Content Based on Method */}
          {paymentMethod === 'manual' ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key="manual"
            >
              {/* QR Code + Address */}
              <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', alignItems: 'center' }}>
                <div
                  style={{
                    width: 140,
                    height: 140,
                    background: 'white',
                    borderRadius: 'var(--radius-lg)',
                    padding: '0.5rem',
                    flexShrink: 0 }}
                >
                  <img src={qrDataUrl} alt="QR Code" style={{ width: '100%', height: '100%' }} />
                </div>
                <div style={{ flex: 1 }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', display: 'block', marginBottom: '0.25rem' }}>
                    آدرس {selectedNetwork.symbol}:
                  </label>
                  <div
                    style={{
                      background: 'var(--color-surface)',
                      border: '1px solid var(--color-border)',
                      borderRadius: 'var(--radius-md)',
                      padding: '0.5rem',
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      wordBreak: 'break-all',
                      marginBottom: '0.5rem' }}
                  >
                    {selectedNetwork.projectAddress}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button
                      onClick={copyAddress}
                      className="btn btn-primary"
                      style={{ flex: 1, padding: '0.5rem', fontSize: '0.75rem' }}
                    >
                      {copied ? <><Check size={14} /> کپی شد!</> : <><Copy size={14} /> کپی آدرس</>}
                    </button>
                    <button
                      onClick={copyPaymentLink}
                      className="btn btn-secondary"
                      style={{ flex: 1, padding: '0.5rem', fontSize: '0.75rem' }}
                    >
                      <QrCode size={14} /> کپی لینک پرداخت
                    </button>
                  </div>
                </div>
              </div>

              {/* Instructions */}
              <div
                style={{
                  background: 'var(--color-surface)',
                  borderRadius: 'var(--radius-lg)',
                  padding: '1rem',
                  fontSize: '0.875rem',
                  lineHeight: 1.8 }}
              >
                <p style={{ fontWeight: 600, marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <AlertCircle size={16} color="var(--color-warning)" />
                  مراحل پرداخت:
                </p>
                <ol style={{ margin: 0, paddingRight: '1.25rem' }}>
                  <li>آدرس بالا را کپی کنید</li>
                  <li>از کیف پول خود <strong>دقیقاً ${amountUsd} USDT</strong> ارسال کنید</li>
                  <li>حتماً از شبکه <strong style={{ color: selectedNetwork.color }}>{selectedNetwork.nameFa}</strong> استفاده کنید</li>
                  <li>پس از تأیید تراکنش، اشتراک شما فعال می‌شود</li>
                </ol>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key="wallet"
            >
              {!walletConnected ? (
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                  <Wallet size={48} style={{ color: 'var(--color-text-tertiary)', marginBottom: '1rem' }} />
                  <p style={{ marginBottom: '1.5rem', color: 'var(--color-text-secondary)' }}>
                    برای پرداخت مستقیم، کیف پول خود را متصل کنید
                  </p>
                  <button
                    onClick={connectWallet}
                    className="btn btn-primary"
                    disabled={isProcessing}
                    style={{ padding: '0.75rem 2rem' }}
                  >
                    {isProcessing ? (
                      <><Loader2 size={16} className="animate-spin" /> در حال اتصال...</>
                    ) : (
                      <><Wallet size={16} /> اتصال MetaMask</>
                    )}
                  </button>
                  <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', marginTop: '1rem' }}>
                    یا از روش "کپی آدرس" برای پرداخت دستی استفاده کنید
                  </p>
                </div>
              ) : (
                <div>
                  <div
                    style={{
                      background: 'var(--color-surface)',
                      borderRadius: 'var(--radius-lg)',
                      padding: '1rem',
                      marginBottom: '1rem' }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <span style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>آدرس کیف پول:</span>
                      <span style={{ fontFamily: 'monospace', fontSize: '0.75rem' }}>
                        {walletAddress.slice(0, 6)}...{walletAddress.slice(-4)}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--color-text-tertiary)', fontSize: '0.875rem' }}>موجودی:</span>
                      <span style={{ fontWeight: 600 }}>{walletBalance} ETH</span>
                    </div>
                  </div>

                  <button
                    onClick={() => {
                      setIsProcessing(true);
                      // در production: فراخوانی contract.transfer
                      setTimeout(() => {
                        const mockHash = '0x' + Array.from({ length: 64 }, () =>
                          Math.floor(Math.random() * 16).toString(16)
                        ).join('');
                        setTxHash(mockHash);
                        setIsProcessing(false);
                        if (onSuccess) onSuccess(mockHash, selectedNetwork.id);
                      }, 2000);
                    }}
                    className="btn btn-primary"
                    disabled={isProcessing}
                    style={{ width: '100%', padding: '1rem' }}
                  >
                    {isProcessing ? (
                      <><Loader2 size={16} className="animate-spin" /> در حال تأیید تراکنش...</>
                    ) : (
                      <>پرداخت ${amountUsd} USDT</>
                    )}
                  </button>
                </div>
              )}
            </motion.div>
          )}

          {/* Success State */}
          {txHash && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              style={{
                marginTop: '1.5rem',
                padding: '1rem',
                background: 'rgba(16, 185, 129, 0.1)',
                border: '1px solid var(--color-success)',
                borderRadius: 'var(--radius-lg)',
                textAlign: 'center' }}
            >
              <Check size={32} color="var(--color-success)" style={{ margin: '0 auto 0.5rem' }} />
              <p style={{ fontWeight: 600, marginBottom: '0.5rem' }}>تراکنش ارسال شد!</p>
              <p style={{ fontSize: '0.75rem', color: 'var(--color-text-tertiary)', fontFamily: 'monospace', wordBreak: 'break-all', marginBottom: '0.5rem' }}>
                {txHash}
              </p>
              <button
                onClick={openExplorer}
                className="btn btn-secondary"
                style={{ fontSize: '0.75rem', padding: '0.5rem 1rem' }}
              >
                <ExternalLink size={14} /> مشاهده در Explorer
              </button>
            </motion.div>
          )}

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              style={{
                marginTop: '1rem',
                padding: '0.75rem',
                background: 'rgba(239, 68, 68, 0.1)',
                border: '1px solid var(--color-error)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--color-error)',
                fontSize: '0.875rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem' }}
            >
              <AlertCircle size={16} />
              {error}
            </motion.div>
          )}

          {/* Security Footer */}
          <div
            style={{
              marginTop: '1.5rem',
              paddingTop: '1rem',
              borderTop: '1px solid var(--color-border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              fontSize: '0.75rem',
              color: 'var(--color-text-tertiary)' }}
          >
            <Shield size={14} />
            <span>پرداخت امن و رمزگذاری‌شده</span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
