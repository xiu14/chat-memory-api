const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const cors = require('cors'); // 添加 CORS 支持

const app = express();

// 允许所有来源的请求
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST'],
  allowedHeaders: ['Content-Type']
}));

app.use(express.json());

// 添加错误处理中间件
app.use((err, req, res, next) => {
  console.error('错误:', err);
  res.status(500).json({ error: err.message });
});

// 添加请求日志
app.use((req, res, next) => {
  console.log(`${new Date().toISOString()} - ${req.method} ${req.url}`);
  next();
});

// 修改数据库连接
const db = new sqlite3.Database('users.db', (err) => {  // 直接使用当前目录
  if (err) {
    console.error('数据库连接失败:', err);
  } else {
    console.log('成功连接到数据库');
  }
});

// 修改数据表结构
db.run(`DROP TABLE IF EXISTS gems`, (err) => {
  if (err) {
    console.error('删除旧表失败:', err);
  } else {
    console.log('旧表删除成功');
    
    // 创建新表，添加 user_id 字段
    db.run(`
      CREATE TABLE IF NOT EXISTS gems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        data TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
      )
    `, (err) => {
      if (err) {
        console.error('创建表失败:', err);
      } else {
        console.log('数据表创建成功');
      }
    });
  }
});

// 修改获取接口，添加更多调试信息
app.get('/api/gems/get/:userId', (req, res) => {
  const userId = req.params.userId;
  console.log('获取用户数据:', userId);
  
  if (!userId) {
    console.log('未提供用户ID');
    res.status(400).json({ error: '未提供用户ID' });
    return;
  }

  // 添加调试查询
  db.all('SELECT * FROM gems', [], (err, allRows) => {
    console.log('所有数据:', allRows);
  });

  db.get('SELECT * FROM gems WHERE user_id = ? ORDER BY id DESC LIMIT 1', [userId], (err, row) => {
    if (err) {
      console.error('获取数据失败:', err);
      res.status(500).json({ error: '获取数据失败' });
      return;
    }
    console.log('查询结果:', row);
    
    if (!row) {
      console.log('未找到数据');
      res.status(404).json({ error: '未找到数据' });
      return;
    }
    
    res.json(row);
  });
});

// 修改保存接口，添加更多调试信息
app.post('/api/gems/save', (req, res) => {
  const { userId, data } = req.body;
  console.log('保存用户数据:', userId);
  console.log('保存的数据:', JSON.stringify(data, null, 2));
  
  if (!userId) {
    console.log('未提供用户ID');
    res.status(400).json({ error: '未提供用户ID' });
    return;
  }

  const dataString = JSON.stringify(data);
  console.log('准备保存的数据字符串:', dataString);

  db.run('INSERT INTO gems (user_id, data, created_at) VALUES (?, ?, datetime("now"))', 
    [userId, dataString], 
    function(err) {
      if (err) {
        console.error('保存数据失败:', err);
        res.status(500).json({ error: '保存数据失败' });
        return;
      }
      console.log('数据保存成功，ID:', this.lastID);
      
      // 验证保存的数据
      db.get('SELECT * FROM gems WHERE id = ?', [this.lastID], (err, row) => {
        if (err) {
          console.error('验证保存数据失败:', err);
        } else {
          console.log('验证保存的数据:', row);
        }
      });
      
      res.json({ success: true, id: this.lastID });
    });
});

// 检查是否有数据
app.get('/api/gems/check', (req, res) => {
  db.get('SELECT COUNT(*) as count FROM gems', [], (err, row) => {
    if (err) {
      console.error('检查数据失败:', err);
      res.status(500).json({ error: '检查数据失败' });
      return;
    }
    res.json({ exists: row.count > 0 });
  });
});

// 添加一个简单的状态检查端点
app.get('/status', (req, res) => {
  res.json({ status: 'ok', time: new Date().toISOString() });
});

// 添加一个检查表结构的端点
app.get('/api/debug/table', (req, res) => {
  db.all(`PRAGMA table_info(gems)`, [], (err, rows) => {
    if (err) {
      console.error('获取表结构失败:', err);
      res.status(500).json({ error: '获取表结构失败' });
      return;
    }
    res.json(rows);
  });
});

// 在文件顶部添加
process.on('SIGINT', () => {
  console.log('正在关闭服务器...');
  db.close(() => {
    console.log('数据库连接已关闭');
    process.exit(0);
  });
});

// 修改端口号
const PORT = process.env.PORT || 3002;  // 改用 3002 端口

const server = app.listen(PORT, () => {
  console.log(`服务器运行在端口 ${PORT}`);
});

// 添加错误处理
server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error(`端口 ${PORT} 已被占用，请先关闭占用该端口的程序`);
    process.exit(1);
  } else {
    console.error('服务器错误:', error);
  }
}); 