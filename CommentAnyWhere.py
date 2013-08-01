import time
import pickle
import sublime, sublime_plugin

class CommentModeOnCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        '''
        comment mode on
        '''
        # set status
        self.view.set_status("comment", "CommentModeOn ReadOnly")

        # set the file as a scratch buffer
        self.view.set_scratch(True)

        # set can be edit
        self.view.set_read_only(False)

        # draw comment
        draw_view(self.view)
        
        # set read only
        self.view.set_read_only(True)

class CommentModeOffCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        '''
        comment mode off
        '''
        # set status
        self.view.set_status("comment", "CommentModeOff Edit")

        # set the file as a scratch buffer
        self.view.set_scratch(False)

        # set can be edit
        self.view.set_read_only(False)

        # reload org file
        file_name = self.view.file_name()
        reload_code(self.view,file_name)

        # easer the comment
        self.view.erase_regions("comment")

class UpdateCommentRegion(sublime_plugin.EventListener):
    '''
    handle save,save the comment to .comment file
    '''
    def on_pre_save(self, view):
        comment = view.get_regions("comment")
        if comment != []:
            view.set_read_only(False)
            comment = collect_comment(view)
            write_comment(view.file_name(),comment)
            easer_view(view)

    def on_post_save(self,view):
        comment = view.get_regions("comment")
        if comment != []:
            draw_view(view)
            view.set_read_only(True)

class InsertCommentCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        comment = self.view.get_regions("comment")
        if comment != []:
            # set status 
            self.view.set_status("comment", "CommentModeOn Inserting")
            
            # set can be edit
            self.view.set_read_only(False)

            now_pos = self.view.sel()[0].begin()
            new_comment = []
            for each in comment:
                if each.begin() > now_pos:
                    new_comment.append(sublime.Region(each.begin()+2,each.end()+2))
                elif each.end() < now_pos:
                    new_comment.append(each)
                elif each.begin() <= now_pos and each.end() >= now_pos:
                    new_comment.append(sublime.Region(each.begin(),each.end()+2))
                else:
                    print each,now_pos
                    assert False
            comment = new_comment
            self.view.insert(edit, now_pos, '<>')
            comment.append(sublime.Region(now_pos,now_pos+2))
            self.view.sel().clear()
            self.view.sel().add(sublime.Region(now_pos+1))

            mark_comment_region(self.view,comment)

def draw_view(view):
    '''
    read code and comment from file and draw on view
    '''
    # read the org file
    file_name = view.file_name()
    reload_code(view,file_name)
    
    # read all comment from .comment file
    comments = read_comment(file_name)
    comments = sorted(comments,key = lambda x:x[0])

    # rebase the comment offset
    new_comments = []
    offset = 0
    for each in comments:
        new_comments.append([each[0]+offset, each[1]])
        offset += len(each[1])
    comments = new_comments

    # insert all comments and log regions
    edit = view.begin_edit()
    try:
        comment_reg = []
        for each_comment in comments:
            start_pos = each_comment[0]
            comment = each_comment[1]
            comment_offset = len(comment)

            view.insert(edit,start_pos,comment)
            comment_reg.append(sublime.Region(start_pos,start_pos+comment_offset))
        else:
            comment_reg.append(sublime.Region(0,0))
    finally:
        view.end_edit(edit)
    mark_comment_region(view,comment_reg)

def mark_comment_region(view,comment_regs):
    '''
    mark comment_regs as comment fmt
    '''
    view.add_regions("comment", comment_regs, "string","bookmark")

def collect_comment(view):
    '''
    collect the "comment" regions
    '''
    comment_list = []
    offset = 0
    comment_reg = view.get_regions("comment")
    for each in comment_reg:
        comment_list.append([each.begin()-offset,view.substr(each)])
        offset += each.size()
    return comment_list

def easer_view(view):
    '''
    easer "comment" regions
    '''
    comment_reg = view.get_regions("comment")
    edit = view.begin_edit()
    try:
        for each in comment_reg[::-1]:
            view.erase(edit,each)
    finally:
        view.end_edit(edit)
    # view.erase_regions("comment")

def reload_code(view,file_name):
    '''
    just reload code from file
    '''
    org_fp = open(file_name,'r')
    try:
        org_file = org_fp.read()
    finally:
        org_fp.close()

    edit = view.begin_edit()
    try:
        view.erase(edit,sublime.Region(0,view.size()))
        view.insert(edit,0,org_file)
    finally:
        view.end_edit(edit)

def read_comment(file_name):
    """
    read the comment from "file_name.comment" file
    it is stored by pickle

    return as a dict like:
    [[0,"comment1"], [2,"comment2"]]
    """
    try:
        comment_fp = open(file_name+'.comment','r')
    except:
        return {}
    all_comment = pickle.load(comment_fp)
    return all_comment

def write_comment(file_name,comment):
    """
    write the comment to "file_name.comment" file
    it is stored by pickle

    the comment should be a dict like:
    [[0,"comment1"], [2,"comment2"]]
    """
    comment_fp = open(file_name+'.comment','w')
    pickle.dump(comment, comment_fp)
    comment_fp.close()

