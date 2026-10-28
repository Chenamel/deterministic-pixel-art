# 六状态像素按钮审阅需求

查看 `images/consumer.png` 和3倍图：三列依次是 `START`、`LOOP`、`EXPORT MAP`；六行依次是 `normal, hover, focus, pressed, selected, disabled`。

- 每枚按钮为 {{WIDTH}}×18px，继承蓝色像素浮雕、右向图标及相应状态标记。允许的按钮宽度为不超过112px的偶数。
- 文字使用 Silkscreen Regular8px单色覆盖；普通文字为 `E5ECEE`，禁用文字为 `8997A5`。文字须完整可读，与边框和状态标记保持间距。
- 同一标签在普通、悬停、焦点、选中、禁用态保持位置；按下态的文字和右向图标一起下移1px。
- 文字由消费端绘制。`atlas.png` 是无文字源图集，按三列两行排列，状态顺序同上。

另外提供目标背景 `1D293D`、浅色背景 `E9EDF2` 的合成图。检查原尺寸辨识度、文字与图标的组合、留白、边框及状态区别，给出有具体位置和理由的建议。

{{COMPARISON}}

将结果保存为 `review.md`，按 `START_HERE.md` 要求交回。
