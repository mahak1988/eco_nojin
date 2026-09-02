import { Result, Button } from 'antd';
import { useNavigate } from 'react-router-dom';
import { ToolOutlined } from '@ant-design/icons';

/**
 * Placeholder for the simulator route.
 * The old HyDroMa simulator was purged; a standard rebuild follows.
 */
export default function SimulatorPlaceholder() {
  const navigate = useNavigate();
  return (
    <div style={{ minHeight: '70vh', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <Result
        status="info"
        icon={<ToolOutlined />}
        title="شبیه‌ساز سه‌بعدی در حال بازسازی است"
        subTitle="نسخه قبلی HyDroMa حذف شد. نسخه جدید با معماری استاندارد و پایدار به‌زودی جایگزین می‌شود."
        extra={
          <Button type="primary" onClick={() => navigate('/')}>
            بازگشت به صفحه اصلی
          </Button>
        }
      />
    </div>
  );
}
