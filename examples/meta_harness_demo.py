from gulliblebench.meta_harness import load_demo_cases, render_meta_demo, run_meta_demo

print(render_meta_demo(run_meta_demo(load_demo_cases())))
