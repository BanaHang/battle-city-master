1、使用方法

1.1、配置环境 开发使用Python2。脚本开发和游戏主体都依赖于pygame，请正确安装pygame，并且确保游戏主体是可以无错误运行的。 然后将脚本文件与游戏主体（tanks.py）放在同一目录下。

1.2、如何使用 完成环境配置后，直接运行脚本文件，选择单人或双人模式，自动开始对战。 点击p键切换手动控制或者自动对战；点击o键显示敌方坦克的详细信息。

1.3、实现的功能 完成玩家坦克的自动寻路和开火（按P键切换自动控制和手动控制），完成了敌机状态的显示（按字母O键显示），在开始页面增加一行指导的动画。

2、设计概要

2.1、主体思路 玩家在游戏中的所有操作包含上下左右的移动以及开火，分别由上下左右方向键和空格键控制。而游戏目标，即过关，就是在保证自己不死以及城堡不被破坏的情况下，消灭所有坦克。 因此要实现的主要功能就是模拟玩家移动到可以攻击敌方坦克的位置，然后开火，同时也要兼顾保护自己和城堡。 在游戏主体的程序中，坦克、障碍物、子弹、城堡都是通过pygame.Rect类去创建对象，控制位置和大小，通过其对应的pygame.Rect对象就可以获得对应的位置信息，然后计算路径去实现攻击。

2.2、主要设计

2.2.1、如何寻路 由于玩家操作坦克只能上下左右移动，移动距离依赖于速度（speed=2）和按键按住时间。参考游戏主体中Tank(Enemy)的设计，通过一个新的pygame.Rect对象去模拟下一步的位置，如果该新位置没有越界，也没有和障碍物碰撞，那么就可以移动到新位置。然后将位置信息放在列表中，在游戏主循环的每一次循环中去更新位置。 参考这个思路，在程序中只要确定下一个要移动的位置，判断是否合理，就可以完成运动的模拟。 由于游戏地图是一个二维的图片，移动通过当前位置向相邻位置移动，所以我通过将整个地图划分为2626的网格图（备注：因为整个地图大小是416px416px，而游戏中障碍物的大小为16px*16px，因此416/16=26），然后通过BFS去搜索路径。 使用BFS的原因是因为，BFS是通过一个出发点向周围扩散的去寻找路径，和坦克移动的状态相近，也是从一个位置向相邻位置去移动的方式。 玩家操控的坦克，可以通过自身的rect对象去获得位置信息，敌方坦克也一样。在寻址中，由于玩家坦克的位置很有可能不是正好站在一个格子的顶点上的，因此先做位置修正，向最近的格子的顶点移动，然后再进行寻址，直到和目标地方坦克的rect对象碰撞为止，即为找到一条路径。

2.2.2、如何判定是否开火 当玩家坦克和地方坦克在一条直线中，且两者之间不存在钢（steel）并且不会破坏自己的城堡的情况下，进行开火。开火调用了Tank类中的fire()函数。 位置信息可以用相应角色的rect对象去获取，然后判断是否在一条直线上。