import React, { useState } from 'react';
import { signInWithEmailAndPassword } from 'firebase/auth';
import { getDoc, doc } from 'firebase/firestore';
import { auth, db } from '../firebase';
import { message } from 'antd';
import { useGem } from '../context/GemContext';
import { Form, Input, Button } from 'antd';
import { getUserGemData } from '../services/userService';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { setGemData } = useGem();

  async function onLogin() {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const user = userCredential.user;
      
      // 使用新的函数获取用户数据
      const gemData = await getUserGemData(user.uid);
      
      if (gemData) {
        setGemData(gemData);
        message.success('成功加载历史数据！');
      } else {
        message.info('暂无历史数据，请抓取数据');
      }
      
      message.success('登录成功！');
    } catch (error) {
      console.error('登录失败:', error);
      message.error(error.message || '登录失败，请重试');
    }
  }

  return (
    <Form onFinish={onLogin}>
      <Form.Item label="邮箱" name="email">
        <Input 
          value={email}
          onChange={e => setEmail(e.target.value)}
        />
      </Form.Item>
      <Form.Item label="密码" name="password">
        <Input.Password
          value={password}
          onChange={e => setPassword(e.target.value)}
        />
      </Form.Item>
      <Form.Item>
        <Button type="primary" htmlType="submit">
          登录
        </Button>
      </Form.Item>
    </Form>
  );
};

export default Login; 