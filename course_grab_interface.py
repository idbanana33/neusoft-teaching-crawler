"""自动选课/抢课的预留接口。

本模块只定义后续开发所需的数据结构和接口，不会发起选课请求，
也不会修改教务系统中的任何数据。
"""

from dataclasses import dataclass
from typing import Protocol, Sequence


@dataclass(frozen=True)
class CourseTarget:
    """目标课程的最小描述。"""

    course_code: str
    course_name: str = ""
    teacher: str = ""
    preferred_classes: Sequence[str] = ()


@dataclass(frozen=True)
class CourseCandidate:
    """从课程查询结果中提取的候选课程。"""

    course_code: str
    course_name: str
    teacher: str = ""
    class_id: str = ""
    capacity: int | None = None
    enrolled: int | None = None


class CourseGrabber(Protocol):
    """后续抢课实现需要遵循的接口。"""

    def find_candidates(self, target: CourseTarget) -> list[CourseCandidate]:
        """查询与目标课程匹配的候选项。"""
        ...

    def preview(self, target: CourseTarget) -> list[CourseCandidate]:
        """仅预览可选课程，不执行选课。"""
        ...

    def enroll(self, candidate: CourseCandidate) -> None:
        """执行选课动作；正式实现前必须增加人工确认和安全校验。"""
        raise NotImplementedError(
            "自动抢课尚未实现；当前版本不会向教务系统提交选课请求。"
        )


class NotImplementedCourseGrabber:
    """安全占位实现：允许开发接口，但禁止真实抢课。"""

    def find_candidates(self, target: CourseTarget) -> list[CourseCandidate]:
        return []

    def preview(self, target: CourseTarget) -> list[CourseCandidate]:
        return self.find_candidates(target)

    def enroll(self, candidate: CourseCandidate) -> None:
        raise NotImplementedError(
            "v0.1.0 仅提供接口预留，不执行自动抢课。"
        )
