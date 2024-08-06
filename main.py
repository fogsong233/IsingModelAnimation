#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import math
import random
from typing import Iterable, Tuple

from manim import *

X_NUMBER = 50
Y_NUMBER = 50
T_start = 273 - 100
T_delta = 1000
T_step = 1
T_final = T_start + T_delta
T = T_start
all_energy: int | None = None
points_in_graph: List[Tuple[float, float]] = []


class ArrowType:
    UP = -1
    DOWN = 1


class ArrowUnit(Arrow):
    def __init__(self, init_type: int, **kwargs):
        super().__init__(**kwargs)
        self._type_records: List[int | None] = [init_type, None]
        self._now_type_index = 0

    # 仅仅是储存，并非立刻更新，要调用when_scanned_and_update()才可以
    def set_type_change(self, new_type: int):
        another_index = (self._now_type_index + 1) % 2
        self._type_records[another_index] = new_type

    def get_now_type(self) -> int:
        return self._type_records[self._now_type_index]

    def when_scanned_and_update(self):
        self._now_type_index = (self._now_type_index + 1) % 2


type ArrowTable = List[List[ArrowUnit]]


def calculate_energy(table: ArrowTable, x: int, y: int, center_arrow: ArrowUnit) -> int:
    left = x - 1 if x > 0 else X_NUMBER - 1
    right = x + 1 if x < X_NUMBER - 1 else 0
    up = y - 1 if y > 0 else Y_NUMBER - 1
    down = y + 1 if y < Y_NUMBER - 1 else 0
    arrow_left = table[y][left]
    arrow_right = table[y][right]
    arrow_up = table[up][x]
    arrow_down = table[down][x]
    energy: int = - center_arrow.get_now_type() * (arrow_left.get_now_type()
                                                   + arrow_right.get_now_type()
                                                   + arrow_up.get_now_type()
                                                   + arrow_down.get_now_type())
    return energy


def update_table_and_get_all_energy(table: ArrowTable) -> float:
    result = 0
    for y, y_lsy in enumerate(table):
        for x, arrow in enumerate(y_lsy):
            arrow.when_scanned_and_update()
            result += calculate_energy(table, x, y, arrow)
    return result / 2


def is_change(energy_before: int, energy_after: int) -> bool:
    k = 0.005  # 玻尔兹曼常数
    a = math.exp(-energy_before / (k * T))
    b = math.exp(-energy_after / (k * T))
    stay_before_possibility = a / (a + b)
    return random.uniform(0, 1) > stay_before_possibility  # 如果为真接受变化


class IsingModel(Scene):
    anim_stack: List[Animation | Iterable[Animation]] = []

    def refresh(self, arrow: ArrowUnit):
        new_type: int | None = None
        match arrow.get_now_type():
            case ArrowType.DOWN:
                self.anim_stack.append(
                    arrow.animate.rotate(axis=Z_AXIS, angle=PI, about_point=arrow.get_center()).set_color(BLUE))
                new_type = ArrowType.UP
            case ArrowType.UP:
                self.anim_stack.append(
                    arrow.animate.rotate(axis=Z_AXIS, angle=PI, about_point=arrow.get_center()).set_color(RED))
                new_type = ArrowType.DOWN
        arrow.set_type_change(new_type)

    def construct(self):
        global T, T_delta, T_final, T_start, all_energy, points_in_graph, T_step
        arrow_unit = ArrowUnit(init_type=ArrowType.DOWN,
                               start=UP,
                               end=DOWN,
                               color=RED,
                               max_stroke_width_to_length_ratio=100,
                               buff=0).scale(0.25)
        table: ArrowTable = [[arrow_unit.copy() for _ in range(X_NUMBER)] for _ in range(Y_NUMBER)]
        arrow_table = MobjectTable(
            table=table,
            line_config={"stroke_opacity": 0},
            v_buff=0.1,
            h_buff=0.1
        ).scale(0.4)
        # layout
        top_layout = VGroup()
        secondary_layout = VGroup()
        right_column_layout = VGroup()
        title = Text("Ising Model Animation").scale(0.5)
        top_layout.add(title, secondary_layout)
        # 右边： 温度显示和强度图

        plane = NumberPlane(
            x_range=(T_start, T_final, T_delta / 4),
            y_range=(-800, 0, 200),
            x_length=4,
            y_length=3,
            axis_config={"include_numbers": True},
        )
        line_graph = VGroup()
        plane.add(line_graph)

        temperature_text = Text(f"Temperature: \n {T}").scale(0.5)
        right_column_layout.add(title, plane, temperature_text)
        right_column_layout.arrange(direction=DOWN)

        secondary_layout.add(arrow_table, right_column_layout)
        secondary_layout.arrange(direction=RIGHT)

        top_layout.arrange(direction=DOWN)
        self.play(FadeIn(top_layout), run_time=2)

        # 温度逐渐递增然后递减
        # 开始循环
        state_flag = 0
        while T >= T_start:
            for y, y_lst in enumerate(table):
                for x, arrow in enumerate(y_lst):
                    energy_before = calculate_energy(table, x, y, arrow)
                    energy_after = - energy_before
                    if is_change(energy_before, energy_after):  # 那就接受变化
                        self.refresh(arrow)
                    else:
                        arrow.set_type_change(arrow.get_now_type())
            # 更新右边栏
            new_point: Tuple[float, float] = (T, update_table_and_get_all_energy(table) / 10)
            if len(points_in_graph) > 0:
                line_graph.add(
                    Line(plane.c2p(*points_in_graph[-1]), plane.c2p(*new_point))
                )
            points_in_graph.append(new_point)
            right_column_layout.remove(temperature_text)
            temperature_text = Text(f"Temperature: \n {T}").scale(0.5)
            right_column_layout.add(temperature_text)
            right_column_layout.arrange(direction=DOWN)
            secondary_layout.arrange()
            secondary_layout.update()
            # 更新温度
            if T >= T_final:  # 从递增到递减
                state_flag = 1
            if state_flag:
                T -= T_step
            else:
                T += T_step
            T = round(T, 1)
            if len(self.anim_stack) > 0:
                self.play(*self.anim_stack, run_time=0.05)
            else:
                print("null")
            self.anim_stack.clear()


with tempconfig({
    "preview": True,
    "quality": "high_quality",
    "disable_caching": True,
}):
    IsingModel().render()
