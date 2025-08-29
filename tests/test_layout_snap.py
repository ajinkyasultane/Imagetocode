from core.layout import snap_to_grid, associate_label_to_input

def test_snap_to_grid_basic():
    b = (30, 100, 450, 140)
    s = snap_to_grid(b, grid_cols=12, container_w=480.0, margin=24.0)
    # Snapped x should lie on grid boundaries within container
    assert s[0] >= 24.0 and s[2] <= 480.0

def test_label_input_association():
    labels = [{{"id": "lbl1", "bbox": (36,100,120,120)}}]
    inputs = [{{"id": "in1", "bbox": (24,130,456,170)}}]
    pairs = associate_label_to_input(labels, inputs, min_overlap=0.4, max_vgap_ratio=0.5)
    assert ("lbl1","in1") in pairs
