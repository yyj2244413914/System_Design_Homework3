-- =============================================================
-- 智能课堂（Intelligent Classroom）· 建库建表
-- 由运行中的数据库直接导出，可重复执行（先删表）
-- 库名：Intelligent_Classroom　端口：2881（OceanBase）
-- =============================================================

CREATE DATABASE IF NOT EXISTS `Intelligent_Classroom` DEFAULT CHARACTER SET utf8mb4;
USE `Intelligent_Classroom`;

-- 按依赖反向清理
DROP TABLE IF EXISTS `chat_room_record`;
DROP TABLE IF EXISTS `chat_record`;
DROP TABLE IF EXISTS `chat_room`;
DROP TABLE IF EXISTS `class_member`;
DROP TABLE IF EXISTS `course`;
DROP TABLE IF EXISTS `role_menu`;
DROP TABLE IF EXISTS `user_role`;
DROP TABLE IF EXISTS `menu`;
DROP TABLE IF EXISTS `role`;
DROP TABLE IF EXISTS `user`;

-- user
CREATE TABLE `user` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户ID',
  `username` varchar(50) NOT NULL COMMENT '用户名',
  `password` varchar(100) NOT NULL COMMENT '密码',
  `major` varchar(50) NOT NULL DEFAULT '' COMMENT '专业',
  `grade` varchar(20) NOT NULL DEFAULT '' COMMENT '年级',
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `uk_user_username` (`username`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 1000031 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '用户';

-- role
CREATE TABLE `role` (
  `role_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '角色ID',
  `role_name` varchar(50) NOT NULL COMMENT '角色名',
  PRIMARY KEY (`role_id`),
  UNIQUE KEY `uk_role_name` (`role_name`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 1000004 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '角色';

-- menu
CREATE TABLE `menu` (
  `menu_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '菜单ID',
  `menu_name` varchar(50) NOT NULL COMMENT '菜单名',
  `menu_url` varchar(200) NOT NULL DEFAULT '' COMMENT '菜单URL',
  PRIMARY KEY (`menu_id`)
) ORGANIZATION INDEX AUTO_INCREMENT = 1000009 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '菜单';

-- user_role
CREATE TABLE `user_role` (
  `user_role_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '用户角色ID',
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `role_id` int(11) NOT NULL COMMENT '角色ID',
  PRIMARY KEY (`user_role_id`),
  CONSTRAINT `fk_ur_role` FOREIGN KEY (`role_id`) REFERENCES `intelligent_classroom`.`role`(`role_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  CONSTRAINT `fk_ur_user` FOREIGN KEY (`user_id`) REFERENCES `intelligent_classroom`.`user`(`user_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  UNIQUE KEY `uk_user_role` (`user_id`, `role_id`) BLOCK_SIZE 16384 LOCAL,
  KEY `idx_ur_role` (`role_id`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 1000001 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '用户角色';

-- role_menu
CREATE TABLE `role_menu` (
  `role_menu_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '角色菜单ID',
  `role_id` int(11) NOT NULL COMMENT '角色ID',
  `menu_id` int(11) NOT NULL COMMENT '菜单ID',
  PRIMARY KEY (`role_menu_id`),
  CONSTRAINT `fk_rm_menu` FOREIGN KEY (`menu_id`) REFERENCES `intelligent_classroom`.`menu`(`menu_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  CONSTRAINT `fk_rm_role` FOREIGN KEY (`role_id`) REFERENCES `intelligent_classroom`.`role`(`role_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  UNIQUE KEY `uk_role_menu` (`role_id`, `menu_id`) BLOCK_SIZE 16384 LOCAL,
  KEY `idx_rm_menu` (`menu_id`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 1000001 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '角色菜单';

-- course
CREATE TABLE `course` (
  `course_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '课程ID',
  `course_name` varchar(80) NOT NULL COMMENT '课程名字',
  `class_time` varchar(80) NOT NULL DEFAULT '' COMMENT '上课时间',
  `classroom` varchar(80) NOT NULL DEFAULT '' COMMENT '教室地点',
  `hours` int(11) NOT NULL DEFAULT '0' COMMENT '课时',
  `credits` decimal(3,1) NOT NULL DEFAULT '0.0' COMMENT '学分',
  PRIMARY KEY (`course_id`)
) ORGANIZATION INDEX AUTO_INCREMENT = 1000004 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '课程';

-- class_member
CREATE TABLE `class_member` (
  `member_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '课堂成员ID',
  `course_id` int(11) NOT NULL COMMENT '课程ID',
  `user_id` int(11) NOT NULL COMMENT '用户ID',
  `role_id` int(11) NOT NULL COMMENT '角色ID（在本课中的身份）',
  PRIMARY KEY (`member_id`),
  CONSTRAINT `fk_cm_role` FOREIGN KEY (`role_id`) REFERENCES `intelligent_classroom`.`role`(`role_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  CONSTRAINT `fk_cm_user` FOREIGN KEY (`user_id`) REFERENCES `intelligent_classroom`.`user`(`user_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  CONSTRAINT `fk_cm_course` FOREIGN KEY (`course_id`) REFERENCES `intelligent_classroom`.`course`(`course_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  UNIQUE KEY `uk_member` (`course_id`, `user_id`) BLOCK_SIZE 16384 LOCAL,
  KEY `idx_cm_user` (`user_id`) BLOCK_SIZE 16384 LOCAL,
  KEY `idx_cm_role` (`role_id`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 1000037 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '课堂成员表';

-- chat_room
CREATE TABLE `chat_room` (
  `room_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '聊天室ID',
  `course_id` int(11) NOT NULL COMMENT '课程ID',
  `create_time` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`room_id`),
  CONSTRAINT `fk_room_course` FOREIGN KEY (`course_id`) REFERENCES `intelligent_classroom`.`course`(`course_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  UNIQUE KEY `uk_room_course` (`course_id`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 1000004 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '课程聊天室';

-- chat_record
CREATE TABLE `chat_record` (
  `record_id` int(11) NOT NULL AUTO_INCREMENT COMMENT '记录ID',
  `member_id` int(11) NOT NULL COMMENT '课堂成员ID',
  `menu_id` int(11) NOT NULL DEFAULT '0' COMMENT '菜单ID（0=普通发言）',
  `content` varchar(2000) NOT NULL DEFAULT '' COMMENT '内容',
  PRIMARY KEY (`record_id`),
  CONSTRAINT `fk_cr_member` FOREIGN KEY (`member_id`) REFERENCES `intelligent_classroom`.`class_member`(`member_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  KEY `idx_cr_member` (`member_id`) BLOCK_SIZE 16384 LOCAL,
  KEY `idx_cr_menu` (`menu_id`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX AUTO_INCREMENT = 2000091 AUTO_INCREMENT_MODE = 'ORDER' DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '聊天记录';

-- chat_room_record
CREATE TABLE `chat_room_record` (
  `room_id` int(11) NOT NULL COMMENT '聊天室ID',
  `record_id` int(11) NOT NULL COMMENT '记录ID',
  PRIMARY KEY (`room_id`, `record_id`),
  CONSTRAINT `fk_crr_record` FOREIGN KEY (`record_id`) REFERENCES `intelligent_classroom`.`chat_record`(`record_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  CONSTRAINT `fk_crr_room` FOREIGN KEY (`room_id`) REFERENCES `intelligent_classroom`.`chat_room`(`room_id`) ON UPDATE RESTRICT ON DELETE RESTRICT ,
  KEY `idx_crr_record` (`record_id`) BLOCK_SIZE 16384 LOCAL
) ORGANIZATION INDEX DEFAULT CHARSET = utf8mb4 ROW_FORMAT = DYNAMIC COMPRESSION = 'zstd_1.3.8' REPLICA_NUM = 1 BLOCK_SIZE = 16384 USE_BLOOM_FILTER = FALSE ENABLE_MACRO_BLOCK_BLOOM_FILTER = FALSE TABLET_SIZE = 134217728 PCTFREE = 0 COMMENT = '课程聊天';
