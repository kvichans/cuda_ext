''' Lib for Plugin
Authors:
    Andrey Kvichansky    (kvichans on github.com)
Version:
    '1.0.2 2016-03-22'
Content
    get_translation     i18n
    dlg_wrapper         Wrapper for dlg_custom: pack/unpack values, h-align controls
ToDo: (see end of file)
'''

import  sys, os, gettext
import  cudatext        as app
import  cudax_lib       as apx
from    cudax_lib   import log

REDUCTS = {'lb'     :'label'
        ,  'ln-lb'  :'linklabel'
        ,  'ed'     :'edit'
        ,  'sp-ed'  :'spinedit'
        ,  'me'     :'memo'
        ,  'bt'     :'button'
        ,  'rd'     :'radio'
        ,  'ch'     :'check'
        ,  'ch-bt'  :'checkbutton'
        ,  'ch-gp'  :'checkgroup'
        ,  'rd-gp'  :'radiogroup'
        ,  'cb'     :'combo'
        ,  'cb-ro'  :'combo_ro'
        ,  'lbx'    :'listbox'
        ,  'ch-lbx' :'checklistbox'
        ,  'lvw'     :'listview'
        ,  'ch-lvw' :'checklistview'
        }

def get_translation(plug_file):
    ''' Part of i18n.
        Full i18n-cycle:
        1. All GUI-string in code are used in form 
            _('')
        2. These string are extracted from code to 
            lang/messages.pot
           with run
            python.exe <pypython-root>\Tools\i18n\pygettext.py -p lang <plugin>.py
        3. Poedit (or same program) create 
            <module>\lang\ru_RU\LC_MESSAGES\<module>.po
           from (cmd "Update from POT") 
            lang/messages.pot
           It allows to translate all "strings"
           It creates (cmd "Save")
            <module>\lang\ru_RU\LC_MESSAGES\<module>.mo
        4. get_translation uses the file to realize
            _('')
    '''
    plug_dir= os.path.dirname(plug_file)
    plug_mod= os.path.basename(plug_dir)
    lng     = app.app_proc(app.PROC_GET_LANG, '')
    lng_mo  = plug_dir+'/lang/{}/LC_MESSAGES/{}.mo'.format(lng, plug_mod)
    if os.path.isfile(lng_mo):
        t   = gettext.translation(plug_mod, plug_dir+'/lang', languages=[lng])
        _   = t.gettext
        t.install()
    else:
        _   =  lambda x: x
    return _

def f(s, *args, **kwargs):return s.format(*args, **kwargs)
def top_plus_for_os(what_control, base_control='edit'):
    ''' Addition for what_top to align text with base.
        Params
            what_control    'check'/'label'/'edit'/'button'/'combo'/'combo_ro'
            base_control    'check'/'label'/'edit'/'button'/'combo'/'combo_ro'
    '''
    if what_control==base_control:
        return 0
    env = sys.platform
    if base_control=='edit': 
        if env=='win32':
            return apx.icase(what_control=='check',    1
                            ,what_control=='label',    3
                            ,what_control=='button',  -1
                            ,what_control=='combo_ro',-1
                            ,what_control=='combo',    0
                            ,True,                     0)
        if env=='linux':
            return apx.icase(what_control=='check',    1
                            ,what_control=='label',    5
                            ,what_control=='button',   1
                            ,what_control=='combo_ro', 0
                            ,what_control=='combo',   -1
                            ,True,                     0)
        if env=='darwin':
            return apx.icase(what_control=='check',    2
                            ,what_control=='label',    3
                            ,what_control=='button',   0
                            ,what_control=='combo_ro', 1
                            ,what_control=='combo',    0
                            ,True,                     0)
        return 0
       #if base_control=='edit'
    return top_plus_for_os(what_control, 'edit') - top_plus_for_os(base_control, 'edit')
   #def top_plus_for_os

def dlg_wrapper(title, w, h, cnts, in_vals={}, focus_cid=None):
    """ Wrapper for dlg_custom. 
        Params
            title, w, h     Title, Width, Height 
            cnts            List of static control properties
                                [{cid:'*', tp:'*', t:1,l:1,w:1,r:1,b;1,h:1, cap:'*', hint:'*', en:'0', props:'*', items:[*], valign_to:'cid'}]
                                cid         (opt)(str) C(ontrol)id. Need only for buttons and conrols with value (and for tid)
                                tp               (str) Control types from wiki or short names
                                t           (opt)(int) Top
                                tid         (opt)(str) Ref to other control cid for horz-align text in both controls
                                l                (int) Left
                                r,b,w,h     (opt)(int) Position. w>>>r=l+w, h>>>b=t+h, b can be omitted
                                cap              (str) Caption for labels and buttons
                                hint        (opt)(str) Tooltip
                                en          (opt)('0'|'1'|True|False) Enabled-state
                                props       (opt)(str) See wiki
                                items            (str|list) String as in wiki. List structure by types:
                                                            [v1,v2,]     For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox
                                                            (head, body) For listview, checklistview 
                                                                head    [(cap,width),(cap,width),]
                                                                body    [[r0c0,r0c1,],[r1c0,r1c1,],[r2c0,r2c1,],]
            in_vals         Dict of start values for some controls 
                                {'cid':val}
            focus           (opt) Control cid for  start focus
        Return
            btn_cid         Clicked control cid
            {'cid':val}     Dict of new values for the same (as in_vals) controls
                                Format of values is same too.
        Short names for types
            lb      label
            ln-lb   linklabel
            ed      edit
            sp-ed   spinedit
            me      memo
            bt      button
            rd      radio
            ch      check
            ch-bt   checkbutton
            ch-gp   checkgroup
            rd-gp   radiogroup
            cb      combo
            cb-ro   combo_ro
            lbx     listbox
            ch-lbx  checklistbox
            lvw     listview
            ch-lvw  checklistview
        Example.
            def ask_number(ask, def_val):
                cnts=[dict(        tp='lb',tid='v',l=3 ,w=70,cap=ask)
                     ,dict(cid='v',tp='ed',t=3    ,l=73,w=70)
                     ,dict(cid='!',tp='bt',t=45   ,l=3 ,w=70,cap='OK',props='1')
                     ,dict(cid='-',tp='bt',t=45   ,l=73,w=70,cap='Cancel')]
                vals={'v':def_val}
                while True:
                    btn,vals=dlg_wrapper('Example',146,75,cnts,vals,'v')
                    if btn is None or btn=='-': return def_val
                    if not re.match(r'\d+$', vals['v']): continue
                    return vals['v']
    """
    pass;                  #LOG and log('in_vals={}',pformat(in_vals, width=120))
    cid2i       = {cnt['cid']:i for i,cnt in enumerate(cnts) if 'cid' in cnt}
    if True:
        # Checks
        no_tids = {cnt['tid']   for   cnt in    cnts    if 'tid' in cnt and  cnt['tid'] not in cid2i}
        if no_tids:
            raise Exception(f('No cid(s) for tid(s): {}', no_tids))
        no_vids = {cid          for   cid in    in_vals if                          cid not in cid2i}
        if no_vids:
            raise Exception(f('No cid(s) for vals: {}', no_vids))
    ctrls_l = []
    for cnt in cnts:
        tp      = cnt['tp']
        tp      = REDUCTS.get(tp, tp)
        lst     = ['type='+tp]
        # Simple props
        for k in ['cap', 'hint', 'props']:
            if k in cnt:
                lst += [k+'='+str(cnt[k])]
        # Props with preparation
        # Position:
        #   t[op] or tid, l[eft] required
        #   w[idth]  >>> r[ight ]=l+w
        #   h[eight] >>> b[ottom]=t+h
        #   b dont need for buttons, edit, labels
        l       = cnt['l']
        t       = cnt.get('t', 0)
        if 'tid' in cnt:
            # cid for horz-align text
            bs_cnt  = cnts[cid2i[cnt['tid']]]
            bs_tp   = bs_cnt['tp']
            t       = bs_cnt['t'] + top_plus_for_os(tp, REDUCTS.get(bs_tp, bs_tp))
        r       = cnt.get('r', l+cnt.get('w', 0)) 
        b       = cnt.get('b', t+cnt.get('h', 0)) 
        lst    += ['pos={l},{t},{r},{b}'.format(l=l,t=t,r=r,b=b)]
        if 'en' in cnt:
            val     = cnt['en']
            lst    += ['en='+('1' if val in [True, '1'] else '0')]

        if 'items' in cnt:
            items   = cnt['items']
            if isinstance(items, str):
                pass
            elif tp in ['listview', 'checklistview']:
                # For listview, checklistview: "\t"-separated items.
                #   first item is column headers: title1+"="+size1 + "\r" + title2+"="+size2 + "\r" +...
                #   other items are data: cell1+"\r"+cell2+"\r"+...
                # ([(hd,wd)], [[cells],[cells],])
                items   = '\t'.join(['\r'.join(['='.join((hd,sz)) for hd,sz in items[0]])]
                                   +['\r'.join(row) for row in items[1]]
                                   )
            else:
                # For combo, combo_ro, listbox, checkgroup, radiogroup, checklistbox: "\t"-separated lines
                items   = '\t'.join(items)
            lst+= ['items='+items]
        
        # Prepare val
        if cnt.get('cid') in in_vals:
            in_val = in_vals[cnt['cid']]
            if False:pass
            elif tp in ['check', 'radio', 'checkbutton'] and isinstance(in_val, bool):
                # For check, radio, checkbutton: value "0"/"1" 
                in_val  = '1' if in_val else '0'
            elif tp=='memo':
                # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(2)) 
                if isinstance(in_val, list):
                    in_val = '\t'.join([v.replace('\t', chr(2)) for v in in_val])
                else:
                    in_val = in_val.replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
            elif tp=='checkgroup' and isinstance(in_val, list):
                # For checkgroup: ","-separated checks (values "0"/"1") 
                in_val = ','.join(in_val)
            elif tp in ['checklistbox', 'checklistview'] and isinstance(in_val, tuple):
                # For checklistbox, checklistview: index+";"+checks 
                in_val = ';'.join( (in_val[0], ','.join( in_val[1]) ) )
            lst+= ['val='+str(in_val)]
        pass;                      #LOG and log('lst={}',lst)
        ctrls_l+= [chr(1).join(lst)]
    pass;                  #LOG and log('ok ctrls_l={}',pformat(ctrls_l, width=120))

    ans     = app.dlg_custom(title, w, h, '\n'.join(ctrls_l), cid2i.get(focus_cid, -1))
    if ans is None: return None, None   # btn_cid, {cid:v}

    btn_i,  \
    vals_ls = ans[0], ans[1].splitlines()
    btn_cid = cnts[btn_i]['cid']
    # Parse output values
    an_vals = {cid:vals_ls[cid2i[cid]] for cid in in_vals}
    for cid in an_vals:
        cnt     = cnts[cid2i[cid]]
        tp      = cnt['tp']
        tp      = REDUCTS.get(tp, tp)
        in_val  = in_vals[cid]
        an_val  = an_vals[cid]
        if False:pass
        elif tp=='memo':
            # For memo: "\t"-separated lines (in lines "\t" must be replaced to chr(2)) 
            if isinstance(in_val, list):
                an_val = [v.replace(chr(2), '\t') for v in an_val.split('\t')]
               #in_val = '\t'.join([v.replace('\t', chr(2)) for v in in_val])
            else:
                an_val = an_val.replace('\t','\n').replace(chr(2), '\t')
               #in_val = in_val.replace('\t', chr(2)).replace('\r\n','\n').replace('\r','\n').replace('\n','\t')
        elif tp=='checkgroup' and isinstance(in_val, list):
            # For checkgroup: ","-separated checks (values "0"/"1") 
            an_val = an_val.split(',')
           #in_val = ','.join(in_val)
        elif tp in ['checklistbox', 'checklistview'] and isinstance(in_val, tuple):
            an_val = an_val.split(';')
            an_val = (an_val[0], an_val[1].split(','))
           #in_val = ';'.join(in_val[0], ','.join(in_val[1]))
        elif isinstance(in_val, bool): 
            an_val = an_val=='1'
        else: 
            an_val = type(in_val)(an_val)
        an_vals[cid]    = an_val
    return  btn_cid, an_vals
   #def dlg_wrapper

if __name__ == '__main__' :     # Tests
    def ask_number(ask, def_val):
        cnts=[dict(        tp='lb',tid='v',l=3 ,w=70,cap=ask)
             ,dict(cid='v',tp='ed',t=3    ,l=73,w=70)
             ,dict(cid='!',tp='bt',t=45   ,l=3 ,w=70,cap='OK',props='1')
             ,dict(cid='-',tp='bt',t=45   ,l=73,w=70,cap='Cancel')]
        vals={'v':def_val}
        while True:
            btn,vals=dlg_wrapper('Example',146,75,cnts,vals,'v')
            if btn is None or btn=='-': return def_val
            if not re.match(r'\d+$', vals['v']): continue
            return vals['v']
    ask_number('ask_____________', '____smth')
