package com.petlumina.backend.controller.admin;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.petlumina.backend.annotation.AuthCheck;
import com.petlumina.backend.common.BaseResponse;
import com.petlumina.backend.common.DeleteRequest;
import com.petlumina.backend.common.ResultUtils;
import com.petlumina.backend.constant.UserConstant;
import com.petlumina.backend.exception.ErrorCode;
import com.petlumina.backend.model.dto.pet.PetQueryRequest;
import com.petlumina.backend.model.entity.Pet;
import com.petlumina.backend.model.entity.User;
import com.petlumina.backend.model.vo.PetVO;
import com.petlumina.backend.service.user.PetService;
import com.petlumina.backend.service.user.UserService;
import com.petlumina.backend.utils.ThrowUtils;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import javax.annotation.Resource;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/v1/admin/pet")
@Slf4j
public class AdminPetController {

    @Resource
    private PetService petService;

    @Resource
    private UserService userService;

    @PostMapping("/list/page/vo")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Page<PetVO>> listPetVOByPage(@RequestBody PetQueryRequest request) {
        ThrowUtils.throwIf(request == null, ErrorCode.PARAMS_ERROR);
        long current = request.getCurrent();
        long size = request.getPageSize();
        QueryWrapper<Pet> queryWrapper = petService.getQueryWrapper(request);
        Page<Pet> page = petService.page(new Page<>(current, size), queryWrapper);
        Page<PetVO> voPage = new Page<>(current, size, page.getTotal());
        voPage.setRecords(page.getRecords().stream().map(pet -> {
            PetVO vo = PetVO.objToVo(pet);
            User owner = userService.getById(pet.getUserId());
            if (owner != null) {
                vo.setUser(com.petlumina.backend.model.vo.UserVO.objToVo(owner));
            }
            return vo;
        }).collect(Collectors.toList()));
        return ResultUtils.success(voPage);
    }

    @PostMapping("/delete")
    @AuthCheck(mustRole = UserConstant.ADMIN_ROLE)
    public BaseResponse<Boolean> deletePet(@RequestBody DeleteRequest request) {
        ThrowUtils.throwIf(request == null || request.getId() <= 0, ErrorCode.PARAMS_ERROR);
        Pet pet = petService.getById(request.getId());
        ThrowUtils.throwIf(pet == null, ErrorCode.NOT_FOUND_ERROR);
        boolean result = petService.removeById(request.getId());
        return ResultUtils.success(result);
    }
}
