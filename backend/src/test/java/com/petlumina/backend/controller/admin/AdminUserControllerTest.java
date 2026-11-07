package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.conditions.Wrapper;
import com.petlumina.backend.exception.BusinessException;
import com.petlumina.backend.model.dto.user.AdminUserSaveRequest;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.Post;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.service.user.PetService;
import com.petlumina.backend.service.user.PostService;
import com.petlumina.backend.service.user.UserService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * E10：管理端「新增/编辑用户」原来只弹 toast，现在必须真落库。
 * 这里只测控制器自己的校验与字段映射，不启 Spring 上下文。
 */
@ExtendWith(MockitoExtension.class)
class AdminUserControllerTest {

    @Mock
    private UserService userService;

    @Mock
    private PetService petService;

    @Mock
    private PostService postService;

    private AdminUserController controller;

    @BeforeEach
    void setUp() {
        controller = new AdminUserController();
        ReflectionTestUtils.setField(controller, "userService", userService);
        ReflectionTestUtils.setField(controller, "petService", petService);
        ReflectionTestUtils.setField(controller, "postService", postService);
    }

    @Test
    void addUserRejectsBadPhone() {
        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setPhone("1234");
        request.setPassword("abc12345");

        BusinessException ex = assertThrows(BusinessException.class, () -> controller.addUser(request));
        assertEquals("手机号格式不正确", ex.getMessage());
    }

    @Test
    void addUserRejectsShortPassword() {
        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setPhone("13900001111");
        request.setPassword("123");

        BusinessException ex = assertThrows(BusinessException.class, () -> controller.addUser(request));
        assertEquals("密码至少 6 位", ex.getMessage());
    }

    @Test
    void addUserRejectsDuplicatePhone() {
        when(userService.count(any(QueryWrapper.class))).thenReturn(1L);
        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setPhone("13900001111");
        request.setPassword("abc12345");

        BusinessException ex = assertThrows(BusinessException.class, () -> controller.addUser(request));
        assertEquals("手机号已存在", ex.getMessage());
    }

    @Test
    void addUserHashesPasswordAndDefaultsNickname() {
        when(userService.count(any(QueryWrapper.class))).thenReturn(0L);
        when(userService.save(any(User.class))).thenAnswer(invocation -> {
            User user = invocation.getArgument(0);
            user.setId(90001L);
            return true;
        });

        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setPhone("13900001111");
        request.setPassword("abc12345");

        Long id = controller.addUser(request).getData();

        ArgumentCaptor<User> captor = ArgumentCaptor.forClass(User.class);
        verify(userService).save(captor.capture());
        User saved = captor.getValue();
        assertEquals(90001L, id);
        assertEquals("用户1111", saved.getNickname());
        assertEquals("user", saved.getRole());
        assertEquals(1, saved.getStatus());
        assertNotEquals("abc12345", saved.getPassword());
        assertTrue(saved.getPassword().startsWith("$2"), "BCrypt 哈希应以 $2 开头");
    }

    @Test
    void updateUserRejectsUnknownRole() {
        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setId(90001L);
        request.setRole("expert");

        BusinessException ex = assertThrows(BusinessException.class, () -> controller.updateUser(request));
        assertEquals("角色只能是 user 或 admin", ex.getMessage());
    }

    @Test
    void updateUserRequiresExistingUser() {
        when(userService.getById(anyLong())).thenReturn(null);
        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setId(90001L);

        BusinessException ex = assertThrows(BusinessException.class, () -> controller.updateUser(request));
        assertEquals("用户不存在", ex.getMessage());
    }

    @Test
    void updateUserKeepsPasswordWhenBlank() {
        User existing = new User();
        existing.setId(90001L);
        existing.setPhone("13900001111");
        existing.setPassword("$2a$10$existing");
        when(userService.getById(90001L)).thenReturn(existing);
        when(userService.updateById(any(User.class))).thenReturn(true);

        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setId(90001L);
        request.setNickname("改名验证");
        request.setStatus(0);

        controller.updateUser(request);

        assertEquals("$2a$10$existing", existing.getPassword());
        assertEquals("改名验证", existing.getNickname());
        assertEquals(0, existing.getStatus());
        verify(userService).updateById(existing);
    }

    @Test
    void updateUserWithoutPasswordChangeNeverRehashes() {
        User existing = new User();
        existing.setId(90002L);
        existing.setPassword("$2a$10$keep");
        when(userService.getById(90002L)).thenReturn(existing);
        when(userService.updateById(any(User.class))).thenReturn(true);

        AdminUserSaveRequest request = new AdminUserSaveRequest();
        request.setId(90002L);

        controller.updateUser(request);

        assertEquals("$2a$10$keep", existing.getPassword());
        verify(userService, never()).count(any(QueryWrapper.class));
    }

    @Test
    void getUserDetailReturnsUserPetsAndPosts() {
        User user = new User();
        user.setId(90003L);
        user.setNickname("森林语者");
        when(userService.getById(90003L)).thenReturn(user);
        when(petService.list(any(Wrapper.class))).thenReturn(List.of(new Pet()));
        when(postService.list(any(Wrapper.class))).thenReturn(List.of(new Post()));

        Map<String, Object> data = controller.getUserDetail(90003L).getData();

        assertNotNull(data.get("user"));
        assertEquals(1, ((List<?>) data.get("pets")).size());
        assertEquals(1, ((List<?>) data.get("posts")).size());
    }
}
