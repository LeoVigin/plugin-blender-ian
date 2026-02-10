import bpy
from bl_ui.space_toolsystem_toolbar import VIEW3D_PT_tools_active, ToolDef
import import_image

def my_hover_log(context, tool, keymap):
    # path = import_image(tool.label) (Source: {path})
    return f"{tool.label}"

def patch_all_tools():
    tools_dict = VIEW3D_PT_tools_active._tools

    for mode, tool_list in tools_dict.items():
        for i, item in enumerate(tool_list):
            if callable(item):
                def wrap_generator(gen=item):
                    def wrapper(context):
                        original_defs = gen(context)
                        new_defs = []
                        for td in original_defs:
                            d = td._asdict()
                            d['description'] = my_hover_log
                            new_defs.append(ToolDef(**d))
                        return tuple(new_defs)
                    return wrapper
                
                tool_list[i] = wrap_generator()

            elif isinstance(item, ToolDef):
                d = item._asdict()
                d['description'] = my_hover_log
                tool_list[i] = ToolDef(**d)

            elif isinstance(item, tuple):
                new_sub_tools = []
                for td in item:
                    d = td._asdict()
                    d['description'] = my_hover_log
                    new_sub_tools.append(ToolDef(**d))
                tool_list[i] = tuple(new_sub_tools)

    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

if __name__ == "__main__":
    patch_all_tools()