package ru.hse.checker.screen;

import com.badlogic.gdx.Gdx;
import com.badlogic.gdx.Screen;
import com.badlogic.gdx.graphics.GL20;

import ru.hse.checker.Game;
import ru.hse.checker.actor.BoardStage;
import ru.hse.checker.controller.io.GuiIO;
import ru.hse.checker.model.Config;
import ru.hse.checker.model.GameModel;

public class GameScreen implements Screen  {

    private BoardStage boardStage;
    private Game game;
    private GameModel gameModel;
    private GuiIO io;

    public GameScreen(Game game) {
        this.game = game;
        gameModel = new GameModel(new Config());
        io = new GuiIO(gameModel);
        boardStage = new BoardStage(io);
        Gdx.input.setInputProcessor(boardStage);
    }

    @Override
    public void show() {
        new Thread(new Runnable() {
            @Override
            public void run() {
                gameModel.startGame(io, boardStage);
            }
        }).start();
    }

    @Override
    public void render(float delta) {
        Gdx.gl.glClearColor(0, 0, 0, 1);
        Gdx.gl.glClear(GL20.GL_COLOR_BUFFER_BIT);
        boardStage.act(Gdx.graphics.getDeltaTime());
        boardStage.draw();
    }

    @Override
    public void resize(int width, int height) {
        boardStage.getViewport().update(width, height, false);
    }

    @Override
    public void pause() {

    }

    @Override
    public void resume() {

    }

    @Override
    public void hide() {

    }

    @Override
    public void dispose() {
        boardStage.dispose();
    }
}
