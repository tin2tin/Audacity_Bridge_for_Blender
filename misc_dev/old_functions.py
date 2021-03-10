def sec_to_frames(sec):
    render = bpy.context.scene.render
    fps = round((render.fps / render.fps_base), 3)
    sec = frames * fps
    return sec