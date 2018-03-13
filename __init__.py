''' Plugin for CudaText editor
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.3.14 2017-08-11'
'''

from .cd_ext import Command as CommandRLS

RLS  = CommandRLS()
class Command:
    def on_focus(self, ed_self):                return RLS.on_focus(ed_self)

    # Nav_cmds
    def on_key_up(self, ed_self, key, state):   return RLS.on_key_up(ed_self, key, state)
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
    def fill_by_str(self):                      return RLS.fill_by_str()
    def insert_char_by_hex(self):               return RLS.insert_char_by_hex()
    
    # Find_repl_cmds
    def find_cb_string_next(self):              return RLS.find_cb_string_next()
    def find_cb_string_prev(self):              return RLS.find_cb_string_prev()
    def replace_all_sel_to_cb(self):            return RLS.replace_all_sel_to_cb()

    def copy_term(self):                        return RLS.copy_term()
    def replace_term(self):                     return RLS.replace_term()
    def expand_sel(self):                       return RLS.expand_sel()
    def expand_sel_copy(self):                  return RLS.expand_sel_copy()
    
#   def mark_all_from(self):                    return RLS.mark_all_from()
#   def count_all_from(self):                   return RLS.count_all_from()
#   def find_first_from(self):                  return RLS.find_first_from()
#   def find_next_from(self):                   return RLS.find_next_from()
#   def find_prev_from(self):                   return RLS.find_prev_from()
#   def repl_next_from(self):                   return RLS.repl_next_from()
#   def repl_stay_from(self):                   return RLS.repl_stay_from()
#   def repl_all_from(self):                    return RLS.repl_all_from()

    def align_in_lines_by_sep(self):            return RLS.align_in_lines_by_sep()
    def reindent(self):                         return RLS.reindent()
    def join_lines(self):                       return RLS.join_lines()
    def del_more_spaces(self):                  return RLS.del_more_spaces()
    def rewrap_sel_by_margin(self):             return RLS.rewrap_sel_by_margin()
    def align_sel_to_center_by_margin(self):    return RLS.align_sel_by_margin('c')
    def align_sel_to_right_by_margin(self):     return RLS.align_sel_by_margin('r')
    def indent_sel_as_1st(self):                return RLS.indent_sel_as_1st()
    def indent_sel_as_bgn(self):                return RLS.indent_sel_as_bgn()
    
    # Jumps_cmds
    def scroll_to_center(self):                 return RLS.scroll_to('cen')
    def scroll_to_top(self):                    return RLS.scroll_to('top')
    def scroll_to_bottom(self):                 return RLS.scroll_to('bot')
    def scroll_to_left(self):                   return RLS.scroll_to('lf')
    def scroll_to_right(self):                  return RLS.scroll_to('rt')
    def jump_to_matching_bracket(self):         return RLS.jump_to_matching_bracket()
    def jump_to_next_mod_lines(self):           return RLS.jump_to_status_line('mod', 'next', 'bgn')
    def jump_to_prev_mod_lines(self):           return RLS.jump_to_status_line('mod', 'prev', 'bgn')
    def jump_to_next_sav_lines(self):           return RLS.jump_to_status_line('svd', 'next', 'bgn')
    def jump_to_prev_sav_lines(self):           return RLS.jump_to_status_line('svd', 'prev', 'bgn')
    def jump_to_next_wrk_lines(self):           return RLS.jump_to_status_line('wrk', 'next', 'bgn')
    def jump_to_prev_wrk_lines(self):           return RLS.jump_to_status_line('wrk', 'prev', 'bgn')
    def jump_to_line_by_cb(self):               return RLS.jump_to_line_by_cb()
    def jump_left_ccsc(self):                   return RLS.jump_ccsc('l', False)
    def jump_right_ccsc(self):                  return RLS.jump_ccsc('r', False)
    def jump_sel_left_ccsc(self):               return RLS.jump_ccsc('l', True)
    def jump_sel_right_ccsc(self):              return RLS.jump_ccsc('r', True)
    def dlg_bms_in_tab(self):                   return RLS.dlg_bms_in_tab()
    def dlg_bms_in_tabs(self):                  return RLS.dlg_bms_in_tabs('a')
    def dlg_nbms_in_tabs(self):                 return RLS.dlg_bms_in_tabs('n')
    
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
#   def edit_strcomment_chars(self):            return RLS.edit_strcomment_chars()
    def rename_file(self):                      return RLS.rename_file()
    def new_file_save_as_near_cur(self):        return RLS.new_file_save_as_near_cur()
    def open_recent(self):                      return RLS.open_recent()
    def open_all_with_subdir(self):             return RLS.open_all_with_subdir()
    def open_with_defapp(self):                 return RLS.open_with_defapp()
    def remove_unprinted(self):                 return RLS.remove_unprinted()

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

    def view_next_tab_from_next_group(self):    return RLS._activate_tab_other_group('next', 'next')
    def view_next_tab_from_prev_group(self):    return RLS._activate_tab_other_group('next', 'prev')
    def view_prev_tab_from_next_group(self):    return RLS._activate_tab_other_group('prev', 'next')
    def view_prev_tab_from_prev_group(self):    return RLS._activate_tab_other_group('prev', 'prev')

    def view_first_tab_from_next_group(self):   return RLS._activate_tab_other_group('frst', 'next')
    def view_first_tab_from_prev_group(self):   return RLS._activate_tab_other_group('frst', 'prev')
    def view_last_tab_from_next_group(self):    return RLS._activate_tab_other_group('last', 'next')
    def view_last_tab_from_prev_group(self):    return RLS._activate_tab_other_group('last', 'prev')
    def go_back(self):                          return RLS.go_back_tab()

    # Paragraph_cmds
    def go_prgph_bgn(self):                      return RLS.go_prgph('bgn')
    def go_prgph_end(self):                      return RLS.go_prgph('end')
    def go_prgph_nxt(self):                      return RLS.go_prgph('nxt')
    def go_prgph_prv(self):                      return RLS.go_prgph('prv')
    
    def align_prgph_cfg(self):                   return RLS.align_prgph('?')
    def align_prgph_l(self):                     return RLS.align_prgph('l')
    def align_prgph_r(self):                     return RLS.align_prgph('r')
    def align_prgph_c(self):                     return RLS.align_prgph('c')
    def align_prgph_f(self):                     return RLS.align_prgph('f')
    
   #class Command
