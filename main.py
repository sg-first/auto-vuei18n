import os
from bs4 import BeautifulSoup
from bs4.element import NavigableString, Comment
from pypinyin import lazy_pinyin

class vueReader:
    def __init__(self, path, file_name):
        self.name = file_name
        self.path = path
        self.full_path = os.path.join(self.path, self.name)
        with open(self.full_path, 'r', encoding='utf-8') as file:
            self.content = file.read()
            self.modifiedContent = self.content
        self.translations = {}

    def __str__(self):
        return f"FILE: {self.name}"

    def write_file(self):
        with open(self.full_path, "w", encoding="utf-8") as actual_file:
            actual_file.write(self.modifiedContent)

    def gatherChineseText(self):
        soup = BeautifulSoup(self.content, 'html.parser')
        # 删除干扰元素
        decomposeElements = soup.find_all(string=lambda text: isinstance(text, Comment)) + soup.find_all('script')
        for i in decomposeElements:
            try:
                i.decompose()
            except AttributeError:
                i.extract()
        # 处理剩下的所有文本
        for element in soup.find_all(text=True):
            if isinstance(element, NavigableString) and self.contains_chinese(element) and (element not in self.translations.keys()):
                    var_name = self.generate_var_name(element)
                    print('varName:', var_name, 'raw:', element)
                    self.translations[element] = var_name
                    # 用 $t(变量名) 替换中文文本
                    self.modifiedContent = self.modifiedContent.replace(str(element), f'{{$t("{var_name}")}}')

    def contains_chinese(self, text):
        # 检查文本中是否包含中文字符
        return any('\u4e00' <= char <= '\u9fff' for char in text)

    def generate_var_name(self, text:str):
        text = text.strip()
        pinyinList = lazy_pinyin(text)
        pinyinList = [i for i in pinyinList if isinstance(i, str) and i.isalpha()] # 删除非字母元素

        varName = ''
        if len(pinyinList) >= 2:
            i = 2
            while i <= len(pinyinList):
                varName = '_'.join(pinyinList[:i])  # 截取前i个字构成变量名
                if varName in self.translations.values():
                    i += 1
                else:
                    return varName
        else:
            varName = pinyinList[0]
        # 检查是否还有重复，如果有，后面加上123
        i = 1
        varNameSuffix = varName
        while varNameSuffix in self.translations.values():
            varNameSuffix = varName + '_' + str(i)
            i += 1
        return varNameSuffix


def generate_localization_file(translations, output_file):
    outputDict = {}
    for moduleName in translations.keys():
        moduleTrans = translations[moduleName]
        # \n替换为\\n，防止输出文本时变成实际的换行
        moduleTrans = {
            text.replace('\n', '\\n') : var_name
                for text, var_name in moduleTrans.items()
        }
        # 转成赋值字符串，varName在前面
        outputDict[moduleName] = {f"\t{var_name}: \"{text}\"," for text, var_name in moduleTrans.items()}
    # 把外层也转成字符串
    retStr = ''
    for moduleName, itemLines in outputDict.items():
        content = '\n'.join(itemLines)
        retStr += moduleName + ': {\n' + content + '\n}\n\n'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(retStr)


base_dir = r"src"  # 指定遍历的根目录
output_localization_file = "localization.js"  # 输出本地化配置文件的路径
all_translations = {}

for root, dirs, files in os.walk(base_dir):
    for filename in files:
        if filename.endswith("vue"):
            vueFile = vueReader(root, filename)
            vueFile.gatherChineseText()
            vueFile.write_file()
            moduleName = filename.replace('.vue', '')
            all_translations[moduleName] = vueFile.translations

print(all_translations)
generate_localization_file(all_translations, output_localization_file)

print("处理完成，生成本地化文件！")
