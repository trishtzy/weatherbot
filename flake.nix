{
  description = "Singapore Weather Telegram Bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
        pythonPkgs = python.pkgs;

        pythonEnv = python.withPackages (ps: with ps; [
          python-telegram-bot
          httpx
          apscheduler
          python-dotenv
        ]);
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [ pythonEnv ];
        };

        packages.default = pythonPkgs.buildPythonApplication {
          pname = "weatherbot";
          version = "0.1.0";
          src = ./.;
          format = "other";

          propagatedBuildInputs = with pythonPkgs; [
            python-telegram-bot
            httpx
            apscheduler
            python-dotenv
          ];

          installPhase = ''
            mkdir -p $out/bin $out/lib
            cp bot.py $out/lib/bot.py
            cat > $out/bin/weatherbot <<EOF
            #!${python}/bin/python
            exec(open("$out/lib/bot.py").read())
            EOF
            chmod +x $out/bin/weatherbot
          '';
        };
      }
    );
}
