#include <QApplication>
#include <QWidget>
#include <QLabel>
#include <QPixmap>

int main(int argc, char *argv[]) {
    QApplication app(argc, argv);

    // 创建主窗口
    QWidget window;
    window.setAttribute(Qt::WA_TranslucentBackground); // 设置窗口背景透明
    window.setWindowFlags(Qt::FramelessWindowHint | Qt::Window); // 去掉窗口边框
    window.resize(400, 800); // 设置窗口大小

    // 添加立绘
    QLabel label(&window);
    QPixmap pixmap("qrc:/tachie/Murasame.v0.2/正常.png"); // 替换为立绘图片路径
    label.setPixmap(pixmap);
    if (pixmap.isNull()) {
        qDebug() << "pic error!";
    } else {
        qDebug() << "pic correct!";
    }
    label.setAlignment(Qt::AlignCenter); // 居中显示
    label.setScaledContents(true); // 图片自适应窗口大小
    label.resize(pixmap.size());   // 根据图片大小调整窗口大小
    label.show();

    window.show();
    return app.exec();
}
