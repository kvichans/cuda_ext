''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '0.9.3 2016-05-16'
'''

from .cd_ext import Command as CommandRLS

RLS  = CommandRLS()
class Command:
    def on_focus(self, ed_self):                return RLS.on_focus(ed_self)

    # Nav_cmds
    def on_console_nav(self, ed_self, text):    return RLS.on_console_nav(ed_self, text)
    def nav_by_console_err(self):               return RLS.nav_by_console_err()
    def open_file_near_right(self):             return RLS._open_file_near('right')
    def open_file_near_left(self):              return RLS._open_file_near('left')
    def open_selected(self):                    return RLS.open_selected()
    
    # Tree_cmds
    def tree_path_to_status(self):              return RLS.tree_path_to_status()
    def set_nearest_tree_node(self):            return RLS.set_nearest_tree_node()
    
    # Insert_cmds
    def add_indented_line_above(self):          return RLS.add_indented_line_above()
    def add_indented_line_below(self):          return RLS.add_indented_line_below()
    def paste_to_1st_col(self):                 return RLS.paste_to_1st_col()
    def paste_with_indent_above(self):          return RLS.paste_with_indent('above')
    def paste_with_indent_below(self):          return RLS.paste_with_indent('below')
    def paste_as_lazarus(self):                 return RLS.paste_with_indent('lazar')
    def align_in_lines_by_sep(self):            return RLS.align_in_lines_by_sep()
    
    # Find_repl_cmds
    def find_cb_string_next(self):              return RLS.find_cb_string_next()
    def find_cb_string_prev(self):              return RLS.find_cb_string_prev()
    def replace_all_sel_to_cb(self):            return RLS.replace_all_sel_to_cb()
    
    # Jumps_cmds
    def scroll_to_center(self):                 return RLS.scroll_to_center()
    def jump_to_matching_bracket(self):         return RLS.jump_to_matching_bracket()
    
    # Move_sep_cmds
    def more_in_tab(self):                      return RLS._move_splitter('into', 1.05)
    def less_in_tab(self):                      return RLS._move_splitter('into', 0.95)
    def more_tree(self):                        return RLS._move_splitter('left', 1.05)
    def less_tree(self):                        return RLS._move_splitter('left', 0.95)
    def more_bottom(self):                      return RLS._move_splitter('bott', 0.95)
    def less_bottom(self):                      return RLS._move_splitter('bott', 1.05)
    def more_main_grp(self):                    return RLS._move_splitter('main', 1.05)
    def less_main_grp(self):                    return RLS._move_splitter('main', 0.95)
    def more_curr_grp(self):                    return RLS._move_splitter('curr', 1.05)
    def less_curr_grp(self):                    return RLS._move_splitter('curr', 0.95)

    # Misc_cmds
    def edit_strcomment_chars(self):            return RLS.edit_strcomment_chars()
    def rename_file(self):                      return RLS.rename_file()

    # Tabs_cmds
    def to_tab_g1_t1(self):                     return RLS._activate_tab(0, 0)
    def to_tab_g1_t2(self):                     return RLS._activate_tab(0, 1)
    def to_tab_g1_t3(self):                     return RLS._activate_tab(0, 2)
    def to_tab_g1_t4(self):                     return RLS._activate_tab(0, 3)
    def to_tab_g1_t5(self):                     return RLS._activate_tab(0, 4)
    def to_tab_g1_t6(self):                     return RLS._activate_tab(0, 5)
    def to_tab_g1_t7(self):                     return RLS._activate_tab(0, 6)
    def to_tab_g1_t8(self):                     return RLS._activate_tab(0, 7)
    def to_tab_g1_t9(self):                     return RLS._activate_tab(0, 8)
    def to_tab_g2_t1(self):                     return RLS._activate_tab(1, 0)
    def to_tab_g2_t2(self):                     return RLS._activate_tab(1, 1)
    def to_tab_g2_t3(self):                     return RLS._activate_tab(1, 2)
    def to_tab_g2_t4(self):                     return RLS._activate_tab(1, 3)
    def to_tab_g2_t5(self):                     return RLS._activate_tab(1, 4)
    def to_tab_g2_t6(self):                     return RLS._activate_tab(1, 5)
    def to_tab_g2_t7(self):                     return RLS._activate_tab(1, 6)
    def to_tab_g2_t8(self):                     return RLS._activate_tab(1, 7)
    def to_tab_g2_t9(self):                     return RLS._activate_tab(1, 8)
    def to_tab_g1_last(self):                   return RLS._activate_last_tab(0)
    def to_tab_g2_last(self):                   return RLS._activate_last_tab(1)
    def to_next_tab(self):                      return RLS._activate_near_tab(1)
    def to_prev_tab(self):                      return RLS._activate_near_tab(-1)
    def move_tab(self):                         return RLS.move_tab()
    def close_tab_from_next_group(self):        return RLS.close_tab_from_other_group('next')
    def close_tab_from_prev_group(self):        return RLS.close_tab_from_other_group('prev')
    def go_back(self):                          return RLS.go_back_tab()
    
   #class Command
