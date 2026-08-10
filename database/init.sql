-- ============================================================================
-- 中小企业智能合同审查平台数据库初始化脚本
-- ============================================================================
--
-- 功能说明:
-- 1. 创建数据库和所有核心表结构
-- 2. 插入默认的系统配置和用户数据
-- 3. 创建视图、存储过程和触发器
-- 4. 设置索引和约束优化查询性能
--
-- 数据库引擎: MySQL 8.0+ / MariaDB 10.5+
-- 字符集: utf8mb4 (支持完整Unicode，包括emoji)
-- 排序规则: utf8mb4_unicode_ci (不区分大小写)
--
-- 执行顺序:
-- 1. 创建数据库
-- 2. 创建表结构
-- 3. 插入初始数据
-- 4. 创建视图和存储过程
-- 5. 创建触发器
-- ============================================================================

-- ============================================================================
-- 第一步：创建数据库
-- ============================================================================
CREATE DATABASE IF NOT EXISTS contract_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE contract_db;

-- ============================================================================
-- 第二步：创建核心表结构
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 用户表 (users)
-- 存储系统用户信息，包括管理员、普通用户和审核员
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID，主键自增',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名，唯一标识',
    email VARCHAR(100) NOT NULL UNIQUE COMMENT '邮箱地址，用于登录和通知',
    hashed_password VARCHAR(255) NOT NULL COMMENT '加密后的密码（bcrypt哈希）',
    full_name VARCHAR(100) COMMENT '用户全名',
    company VARCHAR(100) COMMENT '所属公司/组织',
    role ENUM('admin', 'user', 'reviewer') DEFAULT 'user' COMMENT '用户角色：admin-管理员, user-普通用户, reviewer-审核员',
    is_active BOOLEAN DEFAULT TRUE COMMENT '账户是否激活',
    is_verified BOOLEAN DEFAULT FALSE COMMENT '邮箱是否已验证',
    language VARCHAR(10) DEFAULT 'zh-CN' COMMENT '用户界面语言偏好',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai' COMMENT '用户时区设置',
    last_login DATETIME COMMENT '最后登录时间',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '账户创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    INDEX idx_username (username) COMMENT '用户名索引，加速登录查询',
    INDEX idx_email (email) COMMENT '邮箱索引，加速邮箱相关查询',
    INDEX idx_role (role) COMMENT '角色索引，加速角色筛选'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='系统用户表，存储所有用户账户信息';

-- ----------------------------------------------------------------------------
-- 合同表 (contracts)
-- 存储用户上传的合同文件及其处理状态，是系统的核心业务表
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contracts (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '合同ID，主键自增',
    user_id INT NOT NULL COMMENT '上传用户ID，外键关联users表',
    
    -- 合同基本信息
    title VARCHAR(200) NOT NULL COMMENT '合同标题/名称',
    description TEXT COMMENT '合同描述/备注信息',
    contract_type ENUM('purchase', 'sales', 'service', 'employment', 'lease', 'partnership', 'other') DEFAULT 'other' COMMENT '合同类型：purchase-采购合同, sales-销售合同, service-服务合同, employment-劳动合同, lease-租赁合同, partnership-合作协议, other-其他类型',
    status ENUM('uploaded', 'parsing', 'parsed', 'ai_pending', 'ai_reviewed', 'manual_pending', 'reviewed', 'archived', 'error') DEFAULT 'uploaded' COMMENT '合同处理状态：uploaded-已上传, parsing-解析中, parsed-已解析, ai_pending-待AI审核, ai_reviewed-AI审核完成, manual_pending-待人工审核, reviewed-审核完毕, archived-已归档, error-处理错误',
    
    -- 文件信息
    original_filename VARCHAR(255) NOT NULL COMMENT '原始文件名（用户上传时的文件名）',
    file_path VARCHAR(500) COMMENT '文件存储路径（MinIO或其他对象存储中的路径）',
    file_size INT COMMENT '文件大小（字节）',
    file_type VARCHAR(50) COMMENT '文件类型：pdf, doc, docx, txt等',
    file_hash VARCHAR(64) COMMENT '文件哈希值（SHA-256），用于文件去重和完整性校验',
    
    -- 解析结果
    parsed_text TEXT COMMENT '解析出的纯文本内容',
    parsed_json JSON COMMENT '结构化解析结果（JSON格式，包含段落、条款等结构化信息）',
    page_count INT DEFAULT 0 COMMENT '文档页数（仅对PDF和Word文档有效）',
    word_count INT DEFAULT 0 COMMENT '文档字数统计',
    
    -- 审核信息
    risk_level VARCHAR(20) COMMENT '风险等级：high-高风险, medium-中风险, low-低风险',
    risk_score FLOAT COMMENT '风险评分（0-100分，分数越高风险越大）',
    review_summary TEXT COMMENT '审核摘要/总结',
    
    -- 时间戳
    uploaded_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    parsed_at DATETIME COMMENT '解析完成时间',
    reviewed_at DATETIME COMMENT '审核完成时间',
    archived_at DATETIME COMMENT '归档时间',
    
    -- 外键约束
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_user_id (user_id) COMMENT '用户ID索引，加速按用户查询',
    INDEX idx_status (status) COMMENT '状态索引，加速状态筛选',
    INDEX idx_contract_type (contract_type) COMMENT '合同类型索引，加速类型筛选',
    INDEX idx_uploaded_at (uploaded_at) COMMENT '上传时间索引，加速时间范围查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='合同主表，存储所有上传的合同文件及其处理状态';

-- ----------------------------------------------------------------------------
-- 合同审核记录表 (contract_reviews)
-- 存储合同的AI审核和人工审核结果，支持多轮审核流程
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contract_reviews (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '审核记录ID，主键自增',
    contract_id INT NOT NULL COMMENT '合同ID，外键关联contracts表',
    user_id INT NOT NULL COMMENT '审核用户ID，外键关联users表',
    
    -- 审核结果
    ai_review_result JSON COMMENT 'AI审核原始结果（JSON格式，包含风险点、建议等）',
    manual_review_result JSON COMMENT '人工审核结果（JSON格式，审核员填写的审核意见）',
    final_review_result JSON COMMENT '最终审核结果（JSON格式，综合AI和人工审核的结果）',
    
    -- 风险点和建议
    risk_points JSON COMMENT '识别出的风险点列表（JSON数组格式）',
    suggestions JSON COMMENT '修改建议列表（JSON数组格式）',
    
    -- 审核状态标志
    is_ai_reviewed BOOLEAN DEFAULT FALSE COMMENT '是否已完成AI审核',
    is_manual_reviewed BOOLEAN DEFAULT FALSE COMMENT '是否已完成人工审核',
    is_finalized BOOLEAN DEFAULT FALSE COMMENT '是否已最终确认审核结果',
    
    -- 时间戳
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '审核记录创建时间',
    ai_reviewed_at DATETIME COMMENT 'AI审核完成时间',
    manual_reviewed_at DATETIME COMMENT '人工审核完成时间',
    finalized_at DATETIME COMMENT '最终确认时间',
    
    -- 外键约束
    FOREIGN KEY (contract_id) REFERENCES contracts(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_contract_id (contract_id) COMMENT '合同ID索引，加速按合同查询审核记录',
    INDEX idx_user_id (user_id) COMMENT '用户ID索引，加速按审核员查询',
    INDEX idx_created_at (created_at) COMMENT '创建时间索引，加速时间范围查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='合同审核记录表，存储AI和人工审核的详细结果';


-- ----------------------------------------------------------------------------
-- 风险规则表 (risk_rules)
-- 存储合同风险检测规则，支持AI审核的规则引擎
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS risk_rules (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '规则ID，主键自增',
    rule_name VARCHAR(100) NOT NULL COMMENT '规则名称',
    rule_description TEXT COMMENT '规则详细描述',
    rule_type ENUM('keyword', 'pattern', 'logic') NOT NULL COMMENT '规则类型：keyword-关键词匹配, pattern-模式匹配, logic-逻辑规则',
    rule_content JSON NOT NULL COMMENT '规则内容（JSON格式，包含匹配条件、阈值等）',
    risk_level ENUM('high', 'medium', 'low') NOT NULL COMMENT '风险等级：high-高风险, medium-中风险, low-低风险',
    category VARCHAR(50) COMMENT '规则分类（如：liability-责任条款, payment-付款条款, confidentiality-保密条款等）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '规则是否启用',
    created_by INT NOT NULL COMMENT '创建者ID，外键关联users表',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_risk_level (risk_level) COMMENT '风险等级索引，加速按风险等级查询',
    INDEX idx_category (category) COMMENT '分类索引，加速按分类查询',
    INDEX idx_is_active (is_active) COMMENT '启用状态索引，加速按启用状态查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='风险规则表，存储合同风险检测规则，用于AI审核引擎';

-- ----------------------------------------------------------------------------
-- 审核日志表 (audit_logs)
-- 存储系统操作日志，用于安全审计和操作追踪
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID，主键自增',
    user_id INT COMMENT '操作用户ID，外键关联users表（可为NULL表示匿名操作）',
    action_type VARCHAR(50) NOT NULL COMMENT '操作类型（如：login, logout, contract_upload, contract_review等）',
    resource_type VARCHAR(50) NOT NULL COMMENT '资源类型（如：user, contract, template, rule等）',
    resource_id INT COMMENT '资源ID（操作对象的ID）',
    details JSON COMMENT '操作详情（JSON格式，包含操作的具体参数和结果）',
    ip_address VARCHAR(45) COMMENT '客户端IP地址（支持IPv4和IPv6）',
    user_agent TEXT COMMENT '用户代理（浏览器/客户端信息）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '日志创建时间',
    INDEX idx_user_id (user_id) COMMENT '用户ID索引，加速按用户查询日志',
    INDEX idx_action_type (action_type) COMMENT '操作类型索引，加速按操作类型查询',
    INDEX idx_resource_type (resource_type) COMMENT '资源类型索引，加速按资源类型查询',
    INDEX idx_created_at (created_at) COMMENT '创建时间索引，加速时间范围查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='审核日志表，记录所有系统操作日志，用于安全审计和问题排查';

-- ----------------------------------------------------------------------------
-- 系统配置表 (system_configs)
-- 存储系统运行时配置参数，支持动态配置管理
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_configs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID，主键自增',
    config_key VARCHAR(100) NOT NULL UNIQUE COMMENT '配置键名，唯一标识配置项',
    config_value TEXT COMMENT '配置值，根据config_type存储不同类型的数据',
    config_type ENUM('string', 'number', 'boolean', 'json', 'array') DEFAULT 'string' COMMENT '配置值类型：string-字符串, number-数字, boolean-布尔值, json-JSON对象, array-数组',
    description TEXT COMMENT '配置项详细描述，说明配置的作用和用法',
    is_public BOOLEAN DEFAULT FALSE COMMENT '是否公开配置（公开配置前端可读取，非公开仅后端使用）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '配置创建时间',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
    INDEX idx_config_key (config_key) COMMENT '配置键名索引，加速配置查询'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='系统配置表，存储所有运行时配置参数，支持动态配置管理';

-- 插入默认管理员用户 (密码: admin123)
INSERT INTO users (username, email, hashed_password, full_name, company, role, is_active, is_verified)
VALUES (
    'admin',
    'admin@contract-review.com',
    '$2b$12$zpdDIM3SDKXynwTLY5kOeuMIvrfaNUeJChb415Iprha6r7kdpcpIW', -- bcrypt hash of 'admin123'
    '系统管理员',
    '智能合同审查平台',
    'admin',
    TRUE,
    TRUE
) ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- 插入默认系统配置
INSERT INTO system_configs (config_key, config_value, config_type, description, is_public)
VALUES
    ('system_name', '中小企业智能合同审查平台', 'string', '系统名称', TRUE),
    ('system_version', '1.0.0', 'string', '系统版本', TRUE),
    ('max_upload_size', '52428800', 'number', '最大上传文件大小(字节)', TRUE),
    ('allowed_file_types', '["pdf", "doc", "docx", "txt"]', 'array', '允许上传的文件类型', TRUE),
    ('ai_provider', 'deepseek', 'string', 'AI服务提供商', FALSE),
    ('default_language', 'zh-CN', 'string', '默认语言', TRUE),
    ('session_timeout', '1800', 'number', '会话超时时间(秒)', FALSE)
ON DUPLICATE KEY UPDATE config_value = VALUES(config_value), updated_at = CURRENT_TIMESTAMP;

-- 插入默认风险规则
INSERT INTO risk_rules (rule_name, rule_description, rule_type, rule_content, risk_level, category, is_active, created_by)
VALUES
    ('无限责任条款', '检查合同中是否存在无限责任条款', 'keyword', '{"keywords": ["无限责任", "无限连带责任", "承担全部责任", "无限制责任"], "exclude": ["有限责任"]}', 'high', 'liability', TRUE, 1),
    ('争议解决条款缺失', '检查合同中是否缺少争议解决条款', 'pattern', '{"patterns": ["争议解决", "仲裁", "诉讼", "管辖权"], "required": true}', 'medium', 'dispute', TRUE, 1),
    ('权利义务不对等', '检查合同中权利义务是否对等', 'logic', '{"logic": "check_balance_of_rights"}', 'medium', 'fairness', TRUE, 1),
    ('保密期限过短', '检查保密条款的期限是否过短', 'pattern', '{"patterns": ["保密期限.*[0-2]年", "保密期.*[0-2]年"], "threshold": 3}', 'low', 'confidentiality', TRUE, 1),
    ('付款条款模糊', '检查付款条款是否明确具体', 'keyword', '{"keywords": ["另行约定", "双方协商", "待定", "视情况而定"], "context": "付款"}', 'medium', 'payment', TRUE, 1)
ON DUPLICATE KEY UPDATE updated_at = CURRENT_TIMESTAMP;

-- ============================================================================
-- 第四步：创建视图
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 视图：合同统计视图 (contract_stats)
-- 功能：按用户统计合同数量和状态分布，用于仪表盘展示
-- 字段说明：
--   user_id: 用户ID
--   username: 用户名
--   company: 所属公司
--   total_contracts: 总合同数
--   reviewed_contracts: 已审核合同数
--   parsed_contracts: 已解析合同数
--   error_contracts: 错误合同数
--   avg_risk_score: 平均风险评分
--   last_upload_date: 最后上传时间
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW contract_stats AS
SELECT
    u.id as user_id,
    u.username,
    u.company,
    COUNT(c.id) as total_contracts,
    SUM(CASE WHEN c.status = 'reviewed' THEN 1 ELSE 0 END) as reviewed_contracts,
    SUM(CASE WHEN c.status = 'parsed' THEN 1 ELSE 0 END) as parsed_contracts,
    SUM(CASE WHEN c.status = 'error' THEN 1 ELSE 0 END) as error_contracts,
    AVG(c.risk_score) as avg_risk_score,
    MAX(c.uploaded_at) as last_upload_date
FROM users u
LEFT JOIN contracts c ON u.id = c.user_id
GROUP BY u.id, u.username, u.company;

-- ----------------------------------------------------------------------------
-- 视图：风险分布视图 (risk_distribution)
-- 功能：按日期、合同类型和风险等级统计风险分布，用于风险分析
-- 字段说明：
--   upload_date: 上传日期（仅日期部分）
--   contract_type: 合同类型
--   risk_level: 风险等级
--   count: 合同数量
--   avg_score: 平均风险评分
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW risk_distribution AS
SELECT
    DATE(c.uploaded_at) as upload_date,
    c.contract_type,
    c.risk_level,
    COUNT(*) as count,
    AVG(c.risk_score) as avg_score
FROM contracts c
WHERE c.risk_level IS NOT NULL
GROUP BY DATE(c.uploaded_at), c.contract_type, c.risk_level
ORDER BY upload_date DESC;

-- ============================================================================
-- 第五步：创建存储过程
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 存储过程：GetUserContractStats
-- 功能：获取指定用户的合同统计信息
-- 参数：
--   user_id: 用户ID，需要统计的用户标识
-- 返回字段：
--   total: 总合同数
--   uploaded: 已上传合同数
--   parsed: 已解析合同数
--   reviewed: 已审核合同数
--   error: 错误合同数
--   avg_risk_score: 平均风险评分
-- 使用示例：CALL GetUserContractStats(1);
-- ----------------------------------------------------------------------------
DELIMITER //
CREATE PROCEDURE GetUserContractStats(IN user_id INT)
BEGIN
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN status = 'uploaded' THEN 1 ELSE 0 END) as uploaded,
        SUM(CASE WHEN status = 'parsed' THEN 1 ELSE 0 END) as parsed,
        SUM(CASE WHEN status = 'reviewed' THEN 1 ELSE 0 END) as reviewed,
        SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error,
        AVG(risk_score) as avg_risk_score
    FROM contracts
    WHERE user_id = user_id;
END //
DELIMITER ;

-- ============================================================================
-- 第六步：创建触发器
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 触发器：update_contract_parsed_at
-- 功能：在合同状态更新时自动设置相应的时间戳字段
-- 触发时机：BEFORE UPDATE ON contracts
-- 逻辑说明：
--   1. 当合同状态从非'parsed'变为'parsed'时，设置parsed_at为当前时间
--   2. 当合同状态从非'reviewed'变为'reviewed'时，设置reviewed_at为当前时间
--   3. 当合同状态从非'archived'变为'archived'时，设置archived_at为当前时间
-- 设计目的：自动化时间戳管理，确保状态变更时间准确记录
-- ----------------------------------------------------------------------------
DELIMITER //
CREATE TRIGGER update_contract_parsed_at
BEFORE UPDATE ON contracts
FOR EACH ROW
BEGIN
    IF NEW.status = 'parsed' AND OLD.status != 'parsed' THEN
        SET NEW.parsed_at = NOW();
    END IF;
    
    IF NEW.status = 'reviewed' AND OLD.status != 'reviewed' THEN
        SET NEW.reviewed_at = NOW();
    END IF;
    
    IF NEW.status = 'archived' AND OLD.status != 'archived' THEN
        SET NEW.archived_at = NOW();
    END IF;
END //
DELIMITER ;

-- ----------------------------------------------------------------------------
-- 触发器：log_contract_review
-- 功能：在合同审核记录插入时自动记录审计日志
-- 触发时机：AFTER INSERT ON contract_reviews
-- 逻辑说明：
--   1. 当新的审核记录插入时，自动向audit_logs表插入一条审计日志
--   2. 记录审核ID、AI审核状态和人工审核状态等信息
-- 设计目的：自动化审计跟踪，确保所有审核操作都有完整记录
-- ----------------------------------------------------------------------------
DELIMITER //
CREATE TRIGGER log_contract_review
AFTER INSERT ON contract_reviews
FOR EACH ROW
BEGIN
    INSERT INTO audit_logs (user_id, action_type, resource_type, resource_id, details)
    VALUES (
        NEW.user_id,
        'contract_review',
        'contract',
        NEW.contract_id,
        JSON_OBJECT(
            'review_id', NEW.id,
            'is_ai_reviewed', NEW.is_ai_reviewed,
            'is_manual_reviewed', NEW.is_manual_reviewed
        )
    );
END //
DELIMITER ;

-- 输出完成信息
SELECT '数据库初始化完成' as message;