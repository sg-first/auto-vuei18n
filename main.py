import os
import json
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from pypinyin import lazy_pinyin

class vueReader:
    def __init__(self, path, file_name):
        self.name = file_name
        self.path = path
        full_path = os.path.join(self.path, self.name)
        with open(full_path, 'r', encoding='utf-8') as file:
            self.content = file.read()
        self.translations = {}

        self.lines = []  # 原始的每一行内容
        self.new_lines = []  # 带有翻译变量的每一行内容

    def __str__(self):
        return f"FILE: {self.name}"

    def write_file(self):
        full_path = os.path.join(self.path, self.name)
        with open(full_path, "w", encoding="utf-8") as actual_file:
            actual_file.write("".join(self.new_lines))

    def find_chinese_text(self):
        self.translations = {}
        for line in self.lines:
            # 用 BeautifulSoup 解析每一行
            soup = BeautifulSoup(line, 'html.parser')
            modified_line = line  # 保留原行，可能被修改

            # 遍历所有文本节点
            for element in soup.find_all(text=True):
                if isinstance(element, NavigableString) and self.contains_chinese(element):
                    var_name = self.generate_var_name(element)
                    self.translations[element] = var_name
                    # 用 $t(变量名) 替换中文文本
                    modified_line = modified_line.replace(str(element), f'{{$t("{var_name}")}}')

            self.new_lines.append(modified_line)  # 将修改后的行加入新内容中

    def contains_chinese(self, text):
        # 检查文本中是否包含中文字符
        return any('\u4e00' <= char <= '\u9fff' for char in text)

    def generate_var_name(self, text):
        pinyinList = lazy_pinyin(text)
        i = 1
        while i <= len(pinyinList):
            varName = '_'.join(pinyinList[:i])  # 截取前i个字构成变量名
            if varName in self.translations.values():
                i += 1
            else:
                return varName
        # TODO: 如果还是碰撞，后面应该加上123

def generate_localization_file(translations, output_file):
    # 生成本地化配置文件
    localization_dict = {var_name: str(text) for text, var_name in translations.items()}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(localization_dict, f, ensure_ascii=False, indent=2)

# -- MAIN SCRIPT --

base_dir = r"vue-views"  # 指定遍历的根目录
output_localization_file = "localization.js"  # 输出本地化配置文件的路径
all_translations = {}

for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith("vue"):
            file = vueReader(root, filename)
            file.find_chinese_text()
            file.write_file()
            all_translations.update(file.translations)

# 生成本地化配置文件
generate_localization_file(all_translations, output_localization_file)

print("处理完成，生成本地化文件！")
