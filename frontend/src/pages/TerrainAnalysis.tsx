import React, { useState } from 'react';
import { Card, Typography, Slider, Button, Space } from 'antd';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Box } from '@react-three/drei';

const { Title, Text } = Typography;

// 3D Scene Component
const Scene3D = ({ size }: { size: number }) => {
  return (
    <>
      <ambientLight intensity={0.5} />
      <pointLight position={[10, 10, 10]} />
      <Box args={[size, size, size]} position={[0, 0, 0]}>
        <meshStandardMaterial attach="material" color="orange" />
      </Box>
      <OrbitControls />
    </>
  );
};

const TerrainAnalysis: React.FC = () => {
  const [cubeSize, setCubeSize] = useState<number>(2);

  return (
    <div>
      <Title level={2}>تحلیل زمین</Title>
      <Card style={{ height: '500px' }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text>تنظیم اندازه مکعب: {cubeSize.toFixed(2)}</Text>
          <Slider
            min={0.5}
            max={5}
            step={0.1}
            value={cubeSize}
            onChange={setCubeSize}
          />
          <Button onClick={() => setCubeSize(2)}>بازنشانی اندازه</Button>
        </Space>
      </Card>
      <Card style={{ height: '500px', marginTop: 16 }}>
        <Canvas camera={{ position: [5, 5, 5], fov: 50 }}>
          <Scene3D size={cubeSize} />
        </Canvas>
      </Card>
    </div>
  );
};

export default TerrainAnalysis;