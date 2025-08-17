import os, json, random, sys, re, warnings
import pygame
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOCAB_PATH = os.path.join(BASE_DIR, "vocabulary.js")
pygame.init()
pygame.font.init()
input_rect = pygame.Rect(0, 0, 0, 0)
pygame.key.set_text_input_rect(input_rect)
W, H = 960, 600
SCREEN = pygame.display.set_mode((W, H))
pygame.display.set_caption("今天背单词了吗")
menu_surface = pygame.Surface((W, H))
study_surface = pygame.Surface((W, H))
test_surface = pygame.Surface((W, H))
gameover_surface = pygame.Surface((W, H))
complete_surface = pygame.Surface((W, H))
practice_surface = pygame.Surface((W, H))
CLOCK = pygame.time.Clock()
def textwrap(text, width=18):
    lines = []
    current_line = ""
    for char in text:
        current_line += char
        if len(current_line) >= width and char in "；，,、/ ":
            lines.append(current_line.strip())
            current_line = ""
    if current_line.strip():
        lines.append(current_line.strip())
    return lines
def get_font(size, bold=False):
    font_path1 = os.path.join(BASE_DIR, "assets", "msyh.ttc")
    font_path2 = "C:/Windows/Fonts/msyh.ttc"
    try:
        if os.path.exists(font_path1):
            return pygame.font.Font(font_path1, size)
        elif os.path.exists(font_path2):
            return pygame.font.Font(font_path2, size)
    except Exception:
        pass
    return pygame.font.SysFont("arial", size, bold=bold)
FONT = get_font(26)
BIG = get_font(40, bold=True)
MID = get_font(28, bold=True)
SMALL = get_font(20)
TITLE_FONT = get_font(36, bold=True)
TINY = get_font(16)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (35, 40, 48)
ACCENT = (90, 180, 255)
GREEN = (50, 220, 140)
RED = (255, 80, 80)
YELLOW = (255, 220, 60)
LIGHT_BLUE = (173, 216, 230)
DARK_BLUE = (25, 25, 50)
LIGHT_GRAY = (200, 200, 220)
MENU_BG = (30, 30, 45)
TEXT_COLOR = (240, 240, 255)
PANEL_BG = (30, 35, 50, 230)
def load_beep():
    try:
        return pygame.mixer.Sound(file=os.path.join(BASE_DIR, "assets", "beep.ogg"))
    except Exception:
        return None
hit_sound = load_beep()
correct_sound = load_beep()
mute = False
def play_sound(sound):
    global mute
    if not sound or mute:
        return
    try:
        sound.play()
    except Exception:
        pass
def draw_bg(surface=None):
    target = surface if surface else SCREEN
    for y in range(H):
        c = 25 + int(30 * (y / H))
        pygame.draw.line(target, (20, 20, 35 + c), (0, y), (W, y))
def draw_top_decor(surface=None):
    target = surface if surface else SCREEN
    pygame.draw.rect(target, MENU_BG, (0, 0, W, 80))
    pygame.draw.line(target, ACCENT, (0, 80), (W, 80), 3)
def draw_text(text, font, color, x, y, center=False, surface=None):
    target = surface if surface else SCREEN
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    target.blit(surf, rect)
    return rect
def draw_pill(x, y, w, h, color, surface=None):
    target = surface if surface else SCREEN
    radius = h // 2
    pygame.draw.rect(target, color, (x + radius, y, w - 2 * radius, h), border_radius=radius)
    pygame.draw.circle(target, color, (x + radius, y + radius), radius)
    pygame.draw.circle(target, color, (x + w - radius, y + radius), radius)
def draw_button(text, x, y, w, h, color, txt_color=BLACK, surface=None):
    target = surface if surface else SCREEN
    draw_pill(x, y, w, h, color, target)
    draw_text(text, MID, txt_color, x + w // 2, y + h // 2, center=True, surface=target)
    return pygame.Rect(x, y, w, h)
try:
    with open(VOCAB_PATH, "r", encoding="utf-8") as f:
        js_content = f.read()
        json_str = js_content.replace("export const vocabulary = ", "").strip().rstrip(';')
        DATA = json.loads(json_str)
except FileNotFoundError:
    print(f"错误：未找到词汇文件 {VOCAB_PATH}")
    DATA = {"levels": []}
except json.JSONDecodeError as e:
    print(f"错误：词汇文件 {VOCAB_PATH} 格式不正确 - {e}")
    DATA = {"levels": []}
except Exception as e:
    print(f"加载词汇文件出错：{e}")
    DATA = {"levels": []}
ALL_WORDS = []
for level_words in DATA.get("levels", []):
    ALL_WORDS.extend(level_words)
WORDS_PER_LEVEL = 50
TOTAL_LEVELS = (len(ALL_WORDS) + WORDS_PER_LEVEL - 1) // WORDS_PER_LEVEL
def get_level_words(level_index):
    start = level_index * WORDS_PER_LEVEL
    end = start + WORDS_PER_LEVEL
    return ALL_WORDS[start:end]
class InputLine:
    def __init__(self):
        self.text = ""
        self.composing = ""
        self.caret = True
        self.timer = 0
        self.max_length = 50
        self.correct = None
    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                if self.text:
                    self.text = self.text[:-1]
                elif self.composing:
                    self.composing = ""
                self.correct = None
            elif event.key == pygame.K_RETURN:
                text = (self.text + self.composing).strip()
                self.text = ""
                self.composing = ""
                result = text
                self.correct = None
                return result
            elif event.key == pygame.K_ESCAPE:
                self.text = ""
                self.composing = ""
                return "__ESC__"
        elif event.type == pygame.TEXTINPUT:
            self.text += event.text
            if len(self.text) > self.max_length:
                self.text = self.text[:self.max_length]
            self.correct = None
        elif event.type == pygame.TEXTEDITING:
            self.composing = event.text
            self.correct = None
        return None
    def draw(self, y, surface=None, x_offset=0):
        x, w, h = 100 + x_offset, W - 200 - x_offset, 60
        if self.correct is True:
            bg_color = (100, 255, 150)
        elif self.correct is False:
            bg_color = (255, 100, 100)
        else:
            bg_color = (240, 240, 255)
        shadow_rect = pygame.Rect(x + 3, y + 3, w, h)
        pygame.draw.rect(surface, (0, 0, 0, 50), shadow_rect, border_radius=15)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=15)
        pygame.draw.rect(surface, ACCENT, (x, y, w, h), 3, border_radius=15)
        display_text = self.text
        if self.composing:
            display_text += f"_{self.composing}_"
        display_text += ("|" if self.caret else "")
        draw_text(display_text, MID, (20, 30, 60), x + 16, y + 12, surface=surface)
        self.timer += CLOCK.get_time()
        if self.timer > 500:
            self.caret = not self.caret
            self.timer = 0
    def set_correct(self, is_correct):
        self.correct = is_correct
SCENE_MENU = "menu"
SCENE_STUDY = "study"
SCENE_PRACTICE = "practice"
SCENE_TEST = "test"
SCENE_GAMEOVER = "gameover"
SCENE_COMPLETE = "complete"
current_scene = SCENE_MENU
selected_level = 0
scroll_offset = 0
study_index = 0
practice_needed = 2
practice_count = 0
practice_input = InputLine()
show_word = True
class Monster:
    def __init__(self, entry):
        self.entry = entry
        self.show_english = random.choice([True, False])
        self.x = random.randint(350, W - 80)
        self.y = -40
        self.vy = random.uniform(0.15, 0.25)
        self.hp = 2
        self.eng_hit = False
        self.cn_hit = False
        self.word = entry["word"]
        self.cn_list = entry["meanings"]
        self.flash = 0
        self.spawn_time = pygame.time.get_ticks()
    def update(self, dt):
        self.y += self.vy * dt * 0.06
        if self.flash > 0:
            self.flash -= dt
    def draw(self, surface=None):
        color = (80, 160, 250) if self.flash <= 0 else (255, 255, 255)
        target = surface if surface else SCREEN
        pygame.draw.circle(target, color, (int(self.x), int(self.y)), 25)
        draw_text(str(self.hp), SMALL, BLACK, int(self.x), int(self.y) - 30, center=True, surface=target)
        if self.show_english:
            display_text = f"{self.word} 是？"
        else:
            display_text = f"{self.cn_list[0]}？"
        draw_text(display_text, TINY, WHITE, int(self.x), int(self.y) + 30, center=True, surface=target)
    def apply_hit(self, kind):
        if self.hp <= 0:
            return False
        if self.show_english and kind == "cn":
            self.cn_hit = True
            self.hp -= 1
            self.flash = 200
            play_sound(hit_sound)
            return True
        elif not self.show_english and kind == "eng":
            self.eng_hit = True
            self.hp -= 1
            self.flash = 200
            play_sound(hit_sound)
            return True
        return False
test_input = InputLine()
test_timer = 0
test_time_limit = 1200
test_lives = 3
spawn_cooldown = 0
monsters = []
score = 0
def reset_study():
    global study_index, practice_needed, practice_count, current_scene, show_word
    study_index = 0
    practice_needed = 2
    practice_count = 0
    show_word = True
    current_scene = SCENE_STUDY
def reset_test():
    global test_input, test_timer, test_time_limit, test_lives, spawn_cooldown, monsters, score
    test_input = InputLine()
    test_timer = 0
    test_time_limit = 1200
    test_lives = 3
    spawn_cooldown = 0
    monsters = []
    score = 0
def change_scene(target):
    global current_scene
    current_scene = target
def draw_topbar(title, surface=None):
    target = surface if surface else SCREEN
    pygame.draw.rect(target, MENU_BG, (0, 0, W, 50))
    draw_text(title, MID, WHITE, 20, 15, surface=target)
    mute_text = "M 开启声音" if mute else "M 静音"
    draw_text(f"Esc 返回  |  {mute_text}", TINY, (200, 200, 220), W - 200, 18, surface=target)
def handle_global_events(event):
    global mute, current_scene, scroll_offset, show_word
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_m:
            global mute
            mute = not mute
        if event.key == pygame.K_ESCAPE:
            if current_scene in [SCENE_STUDY, SCENE_PRACTICE, SCENE_TEST]:
                change_scene(SCENE_MENU)
            elif current_scene == SCENE_COMPLETE or current_scene == SCENE_GAMEOVER:
                change_scene(SCENE_MENU)
        if event.key == pygame.K_SPACE and current_scene == SCENE_STUDY:
            show_word = not show_word
    elif event.type == pygame.MOUSEWHEEL and current_scene == SCENE_MENU:
        scroll_offset -= event.y * 50
        max_scroll = max(0, (TOTAL_LEVELS // 2) * 70 - (H - 200))
        scroll_offset = max(0, min(scroll_offset, max_scroll))
def draw_menu_scene():
    global selected_level, scroll_offset
    menu_surface.fill(BLACK)
    draw_bg(menu_surface)
    left_width = W // 3
    pygame.draw.rect(menu_surface, DARK_BLUE, (0, 0, left_width, H))
    draw_text("今天背单词了吗", TITLE_FONT, WHITE, left_width // 2, H // 4, center=True, surface=menu_surface)
    if TOTAL_LEVELS > 0:
        level_text = f"当前选择: 第 {selected_level + 1} 关"
        word_count = len(get_level_words(selected_level))
        word_text = f"单词数量: {word_count} 个"
        draw_text(level_text, MID, LIGHT_BLUE, left_width // 2, H // 2, center=True, surface=menu_surface)
        draw_text(word_text, SMALL, LIGHT_GRAY, left_width // 2, H // 2 + 40, center=True, surface=menu_surface)
    else:
        draw_text("暂无关卡数据", MID, RED, left_width // 2, H // 2, center=True, surface=menu_surface)
    right_x = left_width
    right_width = W - left_width
    rect_top = 20
    rect_height = H - 80 -20
    pygame.draw.rect(menu_surface, (30, 35, 50), (right_x, rect_top, right_width, rect_height))
    draw_text("选择关卡", BIG, WHITE, right_x + right_width // 2, rect_top + 30, center=True, surface=menu_surface)
    if not ALL_WORDS:
        draw_text("未找到词汇数据，请检查vocabulary.js文件", SMALL, RED, 
                 right_x + right_width // 2, H // 2, center=True, surface=menu_surface)
    else:
        cols = 3
        gap = 15
        btn_width, btn_height = 150, 50
        start_x = right_x + (right_width - (cols * btn_width + (cols - 1) * gap)) // 2
        y_start = rect_top 
        mouse_pos = pygame.mouse.get_pos()
        total_levels = TOTAL_LEVELS
        for i in range(total_levels):
            y_pos = y_start + (i // cols) * (btn_height + gap) - scroll_offset
            if y_pos > rect_top + rect_height or y_pos + btn_height < rect_top:
                continue
            rect = pygame.Rect(start_x + (i % cols) * (btn_width + gap), y_pos, btn_width, btn_height)
            if i == selected_level:
                color = (150, 200, 255)
            elif rect.collidepoint(mouse_pos):
                color = (200, 230, 255)
            else:
                color = (180, 210, 245)
            draw_pill(rect.x, rect.y, rect.width, rect.height, color, menu_surface)
            draw_text(f"第 {i+1} 关", SMALL, (20, 40, 80), rect.centerx, rect.centery - 8, center=True, surface=menu_surface)
            level_words = get_level_words(i)
            draw_text(f"{len(level_words)}词", TINY, (40, 70, 120), rect.centerx, rect.centery + 12, center=True, surface=menu_surface)
    mode_area_height = 80
    pygame.draw.rect(menu_surface, (20, 25, 40), (right_x, H - mode_area_height, right_width, mode_area_height))
    btn_width, btn_height = 140, 50
    btn_y = H - mode_area_height + 15
    study_btn = draw_button("学习模式", right_x + right_width//2 - btn_width - 20, btn_y, 
                          btn_width, btn_height, GREEN, (10, 40, 20), menu_surface)
    test_btn = draw_button("闯关模式", right_x + right_width//2 + 20, btn_y, 
                         btn_width, btn_height, YELLOW, (40, 30, 10), menu_surface)
    if TOTAL_LEVELS > 0 and (TOTAL_LEVELS // 2) * 70 > (H - 200):
        tip_text = "使用鼠标滚轮上下滚动"
        vertical_text = "\n".join(list(tip_text)[:10])
        lines = vertical_text.split("\n")
        tip_surfs = [TINY.render(line, True, (180, 180, 200)) for line in lines]
        total_height = sum(s.get_height() for s in tip_surfs)
        x = W - 20
        y = H // 2 - total_height // 2
        for surf in tip_surfs:
            alpha_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
            surf.set_alpha(77)
            alpha_surf.blit(surf, (0, 0))
            menu_surface.blit(alpha_surf, (x, y))
            y += surf.get_height()
    SCREEN.blit(menu_surface, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed(3)[0]
    if click:
        if TOTAL_LEVELS > 0 and mouse_pos[0] > right_x:
            cols = 3 
            gap = 15
            btn_width, btn_height = 150, 50
            start_x = right_x + (right_width - (cols * btn_width + (cols - 1) * gap)) // 2
            y_start = rect_top
            for i in range(TOTAL_LEVELS):
                y_pos = y_start + (i // cols) * (btn_height + gap) - scroll_offset
                if y_pos > rect_top + rect_height or y_pos + btn_height < rect_top:
                    continue
                rect = pygame.Rect(start_x + (i % cols) * (btn_width + gap), y_pos, btn_width, btn_height)
                if rect.collidepoint(mouse_pos):
                    selected_level = i
                    break
        if study_btn.collidepoint(mouse_pos) and TOTAL_LEVELS > 0:
            reset_study()
        if test_btn.collidepoint(mouse_pos) and TOTAL_LEVELS > 0:
            reset_test()
            change_scene(SCENE_TEST)
def draw_study_scene():
    study_surface.fill(BLACK)
    draw_bg(study_surface)
    draw_topbar(' ',study_surface)
    draw_text("拼写练习 - Spelling Practice", MID, TEXT_COLOR, 15, 10, surface=study_surface)
    words = get_level_words(selected_level)
    if words:
        level_text = f"第 {selected_level+1} 关 | 单词 {study_index+1}/{len(words)}"
        draw_text(level_text, SMALL, TEXT_COLOR, W - 255, 55, center=False, surface=study_surface)
    if not words:
        draw_topbar("学习模式", study_surface)
        draw_text("当前关卡没有单词数据", MID, RED, W//2, H//2, center=True, surface=study_surface)
        draw_text("按 Esc 返回", SMALL, (210, 210, 230), W//2, H//2 + 40, center=True, surface=study_surface)
    else:
        if study_index >= len(words):
            change_scene(SCENE_COMPLETE)
            return
        entry = words[study_index]
        draw_text("单词释义:", MID, ACCENT, 50, 160, surface=study_surface)
        y_offset = 210
        meanings = entry["meanings"][:6]
        meanings_bg_height = min(150, len(meanings) * 50)
        pygame.draw.rect(study_surface, (40, 50, 80, 150), (40, 200, W - 80, meanings_bg_height), border_radius=15)
        pygame.draw.rect(study_surface, (100, 150, 255), (40, 200, W - 80, meanings_bg_height), 2, border_radius=15)
        for meaning in meanings:
            wrapped = textwrap(meaning, width=28)
            for line in wrapped:
                draw_text(line, MID, (220, 230, 255), 60, y_offset, surface=study_surface)
                y_offset += 35
        y_offset += 40
        toggle_text = "按空格键隐藏单词" if show_word else "按空格键显示单词"
        draw_text(toggle_text, MID, YELLOW, W//2, y_offset, center=True, surface=study_surface)
        y_offset += 60
        word_bg_color = (80, 120, 200, 150) if show_word else (60, 80, 120, 150)
        pygame.draw.rect(study_surface, word_bg_color, (W//2 - 200, y_offset, 400, 80), border_radius=15)
        pygame.draw.rect(study_surface, (100, 150, 255), (W//2 - 200, y_offset, 400, 80), 2, border_radius=15)
        if show_word:
            draw_text(entry["word"], BIG, (255, 255, 255), W//2, y_offset + 40, center=True, surface=study_surface)
        else:
            draw_text("单词已隐藏", MID, (200, 200, 220), W//2, y_offset + 40, center=True, surface=study_surface)
        y_offset += 110
        progress_width = 300
        progress_height = 20
        progress_x = W//2 - progress_width//2
        progress_y = y_offset
        pygame.draw.rect(study_surface, (60, 70, 100), (progress_x, progress_y, progress_width, progress_height), border_radius=10)
        progress_ratio = (study_index + 1) / len(words)
        fill_width = int(progress_width * progress_ratio)
        pygame.draw.rect(study_surface, GREEN, (progress_x, progress_y, fill_width, progress_height), border_radius=10)
        progress_text = f"{study_index + 1}/{len(words)}"
        draw_text(progress_text, SMALL, TEXT_COLOR, W//2, y_offset + progress_height//2, center=True, surface=study_surface)
        y_offset += 50
        pygame.draw.rect(study_surface, (100, 150, 200), (W//2 - 100, y_offset, 30, 20), border_radius=3)
        pygame.draw.rect(study_surface, (120, 170, 220), (W//2 - 95, y_offset - 5, 20, 5), border_radius=2)
        draw_text("按 Enter 键继续到下一个单词", SMALL, (200, 200, 220), W//2 - 60, y_offset, surface=study_surface)
    SCREEN.blit(study_surface, (0, 0))
def handle_study_events(event):
    global study_index
    if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
        words = get_level_words(selected_level)
        if study_index < len(words) - 1:
            study_index += 1
        else:
            study_index += 1
def draw_complete_scene():
    complete_surface.fill(BLACK)
    draw_bg(complete_surface)
    draw_topbar("学习完成", complete_surface)
    draw_text("恭喜您完成了本关卡的所有单词学习！", BIG, GREEN, W//2, H//3, center=True, surface=complete_surface)
    draw_text("您可以选择：", MID, WHITE, W//2, H//2 - 30, center=True, surface=complete_surface)
    practice_btn = draw_button("练习模式", W//2 - 160, H//2 + 30, 140, 50, YELLOW, (40, 30, 10), complete_surface)
    test_btn = draw_button("闯关模式", W//2 + 20, H//2 + 30, 140, 50, ACCENT, (10, 20, 60), complete_surface)
    menu_btn = draw_button("返回主菜单", W//2 - 100, H//2 + 100, 200, 50, LIGHT_GRAY, BLACK, complete_surface)
    SCREEN.blit(complete_surface, (0, 0))
    mouse_pos = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed(3)[0]
    if click:
        if practice_btn.collidepoint(mouse_pos):
            global practice_count, study_index
            practice_count = 0
            study_index = 0
            change_scene(SCENE_PRACTICE)
        if test_btn.collidepoint(mouse_pos):
            reset_test()
            change_scene(SCENE_TEST)
        if menu_btn.collidepoint(mouse_pos):
            change_scene(SCENE_MENU)
def draw_practice_scene():
    global practice_count, study_index
    practice_surface.fill(BLACK)
    draw_bg(practice_surface)
    draw_topbar(' ',practice_surface)
    draw_text("拼写练习 - Spelling Practice", MID, TEXT_COLOR, 30, 25, surface=practice_surface)
    words = get_level_words(selected_level)
    idx = min(study_index, len(words)-1) if words else 0
    if not words:
        draw_topbar("练习模式", practice_surface)
        draw_text("当前关卡没有单词数据", MID, RED, W//2, H//2, center=True, surface=practice_surface)
        draw_text("按 Esc 返回", SMALL, (210, 210, 230), W//2, H//2 + 40, center=True, surface=practice_surface)
    else:
        if study_index >= len(words):
            draw_topbar("练习完成", practice_surface)
            pygame.draw.circle(practice_surface, GREEN, (W//2, 250), 60, 5)
            pygame.draw.circle(practice_surface, (100, 230, 150, 100), (W//2, 250), 55)
            draw_text("恭喜完成练习!", BIG, GREEN, W//2, 250, center=True, surface=practice_surface)
            draw_text("按 ESC 键返回主菜单", MID, TEXT_COLOR, W//2, 340, center=True, surface=practice_surface)
            for _ in range(30):
                x = random.randint(W//2 - 100, W//2 + 100)
                y = random.randint(200, 300)
                size = random.randint(3, 8)
                color = random.choice([GREEN, YELLOW, ACCENT, (255, 100, 255)])
                pygame.draw.circle(practice_surface, color, (x, y), size)
        else:
            entry = words[idx]
            draw_text(f"练习单词: {entry['word']}", MID, ACCENT, W//2, 110, center=True, surface=practice_surface)
            draw_text("单词释义:", MID, ACCENT, 50, 160, surface=practice_surface)
            y_offset = 210
            meanings = entry["meanings"][:6]
            meanings_bg_height = min(150, len(meanings) * 50)
            pygame.draw.rect(practice_surface, (40, 50, 80, 150), (40, 200, W - 80, meanings_bg_height), border_radius=15)
            pygame.draw.rect(practice_surface, (100, 150, 255), (40, 200, W - 80, meanings_bg_height), 2, border_radius=15)
            for meaning in meanings:
                wrapped = textwrap(meaning, width=28)
                for line in wrapped:
                    draw_text(line, MID, (220, 230, 255), 60, y_offset, surface=practice_surface)
                    y_offset += 35
            y_offset += 40
            progress_text = f"正确次数: {practice_count} / {practice_needed} (错误不计数)"
            draw_text(progress_text, MID, YELLOW, W//2, y_offset, center=True, surface=practice_surface)
            circle_y = y_offset + 50
            circle_radius = 15
            circle_spacing = 50
            start_x = W//2 - (practice_needed - 1) * circle_spacing//2
            for i in range(practice_needed):
                circle_x = start_x + i * circle_spacing
                color = GREEN if i < practice_count else (100, 100, 120)
                pygame.draw.circle(practice_surface, color, (circle_x, circle_y), circle_radius)
                if i < practice_count:
                    pygame.draw.circle(practice_surface, (200, 255, 200), (circle_x, circle_y), circle_radius - 5)
            y_offset += 90
            practice_input.draw(y_offset, practice_surface)
            y_offset += 80
            pygame.draw.rect(practice_surface, (100, 150, 200), (W//2 - 100, y_offset, 30, 20), border_radius=3)
            pygame.draw.rect(practice_surface, (120, 170, 220), (W//2 - 95, y_offset - 5, 20, 5), border_radius=2)
            draw_text("输入英文单词并按 Enter 提交", SMALL, (200, 200, 220), W//2 - 60, y_offset, surface=practice_surface)
    SCREEN.blit(practice_surface, (0, 0))
def handle_practice_events(event):
    global practice_count, study_index
    words = get_level_words(selected_level)
    if not words:
        return
    if study_index >= len(words):
        return
    idx = min(study_index, len(words)-1)
    entry = words[idx]
    result = practice_input.handle_event(event)
    if result is None:
        return
    if result == "__ESC__": 
        change_scene(SCENE_MENU)
        return
    if result == "":
        return
    def normalize(s):
        return re.sub(r"[^a-z]", "", s.lower())
    is_correct = normalize(result) == normalize(entry["word"])
    practice_input.set_correct(is_correct)
    if is_correct:
        practice_count += 1
        play_sound(correct_sound)
        if practice_count >= practice_needed:
            practice_count = 0
            study_index += 1
            if study_index >= len(words):
                study_index = len(words)
def draw_test_scene(dt):
    global test_timer, spawn_cooldown, test_lives, score
    test_surface.fill(BLACK)
    draw_bg(test_surface)
    words = get_level_words(selected_level)
    draw_topbar(f"闯关模式 - 第 {selected_level+1} 关", test_surface)
    panel_width = 300
    panel_height = H - 50
    pygame.draw.rect(test_surface, PANEL_BG, (0, 50, panel_width, panel_height))
    pygame.draw.line(test_surface, ACCENT, (panel_width, 50), (panel_width, H), 2)
    test_timer += dt / 1000.0
    remaining = max(0, int(test_time_limit - test_timer))
    minutes = remaining // 60
    seconds = remaining % 60
    draw_text(f"时间：{minutes}:{seconds:02d}", MID, WHITE, 30, 80, surface=test_surface)
    draw_text(f"生命：{'❤' * test_lives}", MID, RED, 30, 110, surface=test_surface)
    draw_text(f"得分：{score}", MID, YELLOW, 30, 140, surface=test_surface)
    draw_text("游戏说明：", SMALL, ACCENT, 30, 180, surface=test_surface)
    instructions = [
        "1. 怪物会显示英文单词",
        "   或中文释义",
        "2. 显示英文时，请输入",
        "   对应的中文释义",
        "3. 显示中文时，请输入",
        "   对应的英文单词",
        "4. 输入后按回车攻击",
        "5. 怪物到达底部会扣血"
    ]
    y_pos = 210
    for instr in instructions:
        draw_text(instr, TINY, WHITE, 30, y_pos, surface=test_surface)
        y_pos += 25
    if remaining <= 0:
        change_scene(SCENE_GAMEOVER)
        return
    spawn_cooldown -= dt
    if spawn_cooldown <= 0 and words:
        available = [w for w in words if w not in [m.entry for m in monsters]]
        if not available:
            available = words[:]
        entry = random.choice(available)
        monsters.append(Monster(entry))
        spawn_cooldown = random.randint(3000, 5000)
    current_time = pygame.time.get_ticks()
    for monster in monsters[:]:
        monster.update(dt)
        monster.draw(test_surface)
        if monster.y >= H - 20 and monster.hp > 0 or (current_time - monster.spawn_time) > 30000:
            monsters.remove(monster)
            test_lives -= 1
            if test_lives <= 0:
                change_scene(SCENE_GAMEOVER)
    test_input.draw(H - 60, test_surface, x_offset=panel_width)
    SCREEN.blit(test_surface, (0, 0))
def normalize_english(s):
    return re.sub(r"[^a-z]", "", s.lower())
def match_chinese(user_input, chinese_list):
    user = user_input.strip()
    for meaning in chinese_list:
        if user and user in meaning:
            return True
    return False
def handle_test_events(event):
    global score
    result = test_input.handle_event(event)
    if result is None:
        return
    if result == "__ESC__":
        change_scene(SCENE_MENU)
        return
    if result == "":
        return
    user_english = normalize_english(result)
    hit_any = False
    for monster in monsters:
        if monster.hp <= 1:
            continue
        if monster.show_english:
            if match_chinese(result, monster.cn_list):
                if monster.apply_hit("cn"):
                    score += 5
                    hit_any = True
        else:
            if user_english and normalize_english(monster.word) == user_english:
                if monster.apply_hit("eng"):
                    score += 5
                    hit_any = True
    if hit_any:
        for monster in monsters[:]:
            if monster.hp <= 1:
                monsters.remove(monster)
def draw_gameover_scene():
    gameover_surface.fill(BLACK)
    draw_bg(gameover_surface)
    draw_topbar("游戏结束", gameover_surface)
    draw_text("游戏结束", BIG, RED, W//2, H//2 - 60, center=True, surface=gameover_surface)
    draw_text(f"最终得分：{score}", MID, YELLOW, W//2, H//2 + 10, center=True, surface=gameover_surface)
    draw_text("按 Esc 返回主菜单", SMALL, (220, 230, 255), W//2, H//2 + 60, center=True, surface=gameover_surface)
    menu_btn = draw_button("返回主菜单", W//2 - 100, H//2 + 120, 200, 50, LIGHT_GRAY, BLACK, gameover_surface)
    mouse_pos = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed(3)[0]
    if click and menu_btn.collidepoint(mouse_pos):
        change_scene(SCENE_MENU)
    SCREEN.blit(gameover_surface, (0, 0))
def main():
    global current_scene
    running = True
    while running:
        dt = CLOCK.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            handle_global_events(event)
            if current_scene == SCENE_STUDY:
                handle_study_events(event)
            elif current_scene == SCENE_PRACTICE:
                handle_practice_events(event)
            elif current_scene == SCENE_TEST:
                handle_test_events(event)
        if current_scene == SCENE_MENU:
            draw_menu_scene()
        elif current_scene == SCENE_STUDY:
            draw_study_scene()
        elif current_scene == SCENE_PRACTICE:
            draw_practice_scene()
        elif current_scene == SCENE_TEST:
            draw_test_scene(dt)
        elif current_scene == SCENE_GAMEOVER:
            draw_gameover_scene()
        elif current_scene == SCENE_COMPLETE:
            draw_complete_scene()
        pygame.display.flip()
    pygame.quit()
    sys.exit()
if __name__ == "__main__":
    main()
