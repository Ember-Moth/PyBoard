"""管理端控制器包。

所有 admin 路由统一用 `/api/v1/admin/...` 前缀，并通过 router 级 dependencies 注入
`get_current_admin` 守卫，子模块无需在每个路由上重复声明。
"""
