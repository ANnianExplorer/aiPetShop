package com.petlumina.backend.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.RateLimiter;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.pet.PetAddRequest;
import com.petlumina.backend.model.dto.pet.PetEditRequest;
import com.petlumina.backend.model.dto.pet.PetQueryRequest;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.PetVO;
import com.petlumina.backend.service.PetService;
import com.petlumina.backend.service.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.BeanUtils;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import javax.servlet.http.HttpServletRequest;
import java.util.List;
import java.util.stream.Collectors;

/**
 * 宠物控制器
 */
@RestController
@RequestMapping("/api/v1/pet")
@Slf4j
public class PetController {

    @Resource
    private PetService petService;

    @Resource
    private UserService userService;

    /**
     * 添加宠物
     */
    @PostMapping("/add")
    @RateLimiter(key = "pet_add", time = 60, count = 5, message = "添加宠物操作过于频繁")
    public BaseResponse<Long> addPet(@RequestBody PetAddRequest request,
                                     HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        ThrowUtils.throwIf(request.getName() == null || request.getName().isBlank(), ErrorCode.PARAMS_ERROR, "宠物名称不能为空");

        User loginUser = userService.getLoginUser(httpRequest);

        Pet pet = new Pet();
        BeanUtils.copyProperties(request, pet);

        long petId = petService.addPet(pet, loginUser);
        log.info("添加宠物成功: petId={}, userId={}", petId, loginUser.getId());
        return ResultUtils.success(petId);
    }

    /**
     * 删除宠物
     */
    @PostMapping("/delete")
    public BaseResponse<Boolean> deletePet(@RequestBody DeleteRequest request,
                                           HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        boolean result = petService.deletePet(request.getId(), loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 编辑宠物
     */
    @PostMapping("/edit")
    public BaseResponse<Boolean> editPet(@RequestBody PetEditRequest request,
                                         HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null || request.getId() == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);

        Pet pet = new Pet();
        BeanUtils.copyProperties(request, pet);

        boolean result = petService.editPet(pet, loginUser);
        return ResultUtils.success(result);
    }

    /**
     * 获取宠物详情 (VO)
     */
    @GetMapping("/get/vo")
    public BaseResponse<PetVO> getPetVO(@RequestParam long id,
                                        HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        Pet pet = petService.getById(id);
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR);
        ThrowUtils.throwIf(!pet.getUserId().equals(loginUser.getId())
                && !userService.isAdmin(loginUser), ErrorCode.NO_AUTH_ERROR);
        PetVO vo = PetVO.objToVo(pet);
        // 填充用户信息
        User user = userService.getById(pet.getUserId());
        if (user != null) {
            vo.setUser(com.petlumina.backend.model.vo.UserVO.objToVo(user));
        }
        return ResultUtils.success(vo);
    }

    /**
     * 获取当前用户宠物列表
     */
    @GetMapping("/list")
    public BaseResponse<List<PetVO>> listPets(HttpServletRequest httpRequest) {
        User loginUser = userService.getLoginUser(httpRequest);
        QueryWrapper<Pet> queryWrapper = new QueryWrapper<>();
        queryWrapper.eq("user_id", loginUser.getId());
        queryWrapper.orderByDesc("create_time");
        List<Pet> pets = petService.list(queryWrapper);

        List<PetVO> voList = pets.stream().map(PetVO::objToVo).collect(Collectors.toList());
        return ResultUtils.success(voList);
    }

    /**
     * 宠物分页查询 (当前用户的)
     */
    @PostMapping("/list/page/vo")
    public BaseResponse<com.baomidou.mybatisplus.core.metadata.IPage<PetVO>> listPetVOByPage(
            @RequestBody PetQueryRequest request,
            HttpServletRequest httpRequest) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        User loginUser = userService.getLoginUser(httpRequest);
        // 只查当前用户的宠物
        request.setUserId(loginUser.getId());

        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Pet> queryWrapper = petService.getQueryWrapper(request);
        Page<Pet> page = petService.page(new Page<>(current, size), queryWrapper);

        Page<PetVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(PetVO::objToVo).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }
}
