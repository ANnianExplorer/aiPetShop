package com.petlumina.backend.constant;

/**
 * COS 存储路径常量
 * 统一管理各类文件的存储目录前缀
 */
public interface CosConstant {

    /** 用户头像 */
    String AVATAR_USER = "avatar/user";

    /** 宠物头像 */
    String AVATAR_PET = "avatar/pet";

    /** 帖子图片 */
    String POST_IMAGE = "post/image";

    /** 宠物照片 */
    String PET_IMAGE = "pet/image";

    /** 生活记录图片 */
    String LOG_IMAGE = "log/image";

    /** 通用文件 */
    String COMMON = "common";
}
