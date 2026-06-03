package com.petlumina.backend.manager.cos;

import com.qcloud.cos.COSClient;
import com.qcloud.cos.ClientConfig;
import com.qcloud.cos.auth.BasicCOSCredentials;
import com.qcloud.cos.auth.COSCredentials;
import com.qcloud.cos.http.HttpProtocol;
import com.qcloud.cos.model.PutObjectRequest;
import com.qcloud.cos.model.PutObjectResult;
import com.qcloud.cos.region.Region;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;
import java.io.File;
import java.io.InputStream;

/**
 * 腾讯云 COS 管理器
 */
@Slf4j
@Component
public class CosManager {

    @Value("${cos.secretId}")
    private String secretId;

    @Value("${cos.secretKey}")
    private String secretKey;

    @Value("${cos.bucket}")
    private String bucket;

    @Value("${cos.region}")
    private String region;

    @Value("${cos.host:}")
    private String host;

    private COSClient cosClient;

    @PostConstruct
    public void init() {
        if (secretId == null || secretId.startsWith("your_")) {
            log.warn("COS 凭证未配置，文件上传功能不可用");
            return;
        }
        COSCredentials credentials = new BasicCOSCredentials(secretId, secretKey);
        ClientConfig clientConfig = new ClientConfig(new Region(region));
        clientConfig.setHttpProtocol(HttpProtocol.https);
        cosClient = new COSClient(credentials, clientConfig);
        log.info("COS 客户端初始化成功, bucket={}, region={}", bucket, region);
    }

    /**
     * 上传文件（InputStream）
     */
    public String upload(String key, InputStream inputStream) {
        checkClient();
        PutObjectRequest request = new PutObjectRequest(bucket, key, inputStream, null);
        cosClient.putObject(request);
        return buildUrl(key);
    }

    /**
     * 上传文件（File）
     */
    public String uploadFile(String key, File file) {
        checkClient();
        PutObjectRequest request = new PutObjectRequest(bucket, key, file);
        cosClient.putObject(request);
        return buildUrl(key);
    }

    /**
     * 删除文件
     */
    public void delete(String key) {
        checkClient();
        cosClient.deleteObject(bucket, key);
    }

    /**
     * 构建访问 URL
     * 优先使用自定义域名，否则使用默认 COS 域名
     */
    private String buildUrl(String key) {
        if (host != null && !host.isEmpty()) {
            return host + "/" + key;
        }
        return String.format("https://%s.cos.%s.myqcloud.com/%s", bucket, region, key);
    }

    private void checkClient() {
        if (cosClient == null) {
            throw new RuntimeException("COS 客户端未初始化，请检查配置");
        }
    }
}
